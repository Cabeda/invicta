// Pure, deliberately small population what-if model. This is not a SUMO forecast.
(function (root) {
  const modes = ['car', 'bus', 'metro', 'train', 'bicycle', 'walk', 'motorcycle', 'other'];
  const defaults = {
    population: 1861727, mobileShare: 70, tripsPerMobile: 2.72, demandBasis: 'population',
    affectedShare: 1, externalTrips: 0, preset: 'amp2017', nonresidentShare: 65,
    workShare: 40, shoppingShare: 20, leisureShare: 20,
    shift: 25, toBus: 70, toBicycle: 20, removalEffect: 90,
    residentDetour: 3, visitorDetour: 5, congestionMinutes: 10, exponent: 2,
    busGain: 8, boardingPenalty: 2, capacityGrowth: 150, carOccupancy: 1.5,
    times: { car: 35, bus: 45, metro: 30, train: 45, bicycle: 22, walk: 15, motorcycle: 28, other: 35 }
  };
  function normalize(values) {
    const total = modes.reduce((n, key) => n + (values[key] || 0), 0);
    return Object.fromEntries(modes.map(key => [key, (values[key] || 0) / total]));
  }
  function run(input, facts, shiftOverride) {
    const p = { ...defaults, ...input, times: { ...defaults.times, ...input.times } };
    if (p.workShare + p.shoppingShare + p.leisureShare > 100.00001 || p.toBus + p.toBicycle > 100.00001) return { error: 'shares' };
    const preset = facts.presets[p.preset], mix = normalize(preset.shares);
    const residentDaily = p.demandBasis === 'historic' ? facts.historicDailyTrips : p.population * p.mobileShare / 100 * p.tripsPerMobile;
    const totalDaily = residentDaily + p.externalTrips;
    const requests = totalDaily * p.affectedShare / 100;
    const baseCounts = Object.fromEntries(modes.map(k => [k, requests * mix[k]]));
    const s = Math.max(0, Math.min(.6, (shiftOverride ?? p.shift) / 100));
    const switched = baseCounts.car * s;
    const added = { bus: switched * p.toBus / 100, bicycle: switched * p.toBicycle / 100,
      walk: switched * (100 - p.toBus - p.toBicycle) / 100 };
    const counts = { ...baseCounts, car: baseCounts.car - switched,
      bus: baseCounts.bus + added.bus, bicycle: baseCounts.bicycle + added.bicycle, walk: baseCounts.walk + added.walk };
    const carPressure = Math.max(0, 1 - s * p.removalEffect / 100);
    const congestion = Math.min(p.congestionMinutes, p.times.car) * carPressure ** p.exponent;
    const carCommon = p.times.car - Math.min(p.congestionMinutes, p.times.car) + congestion;
    const busMinutes = Math.max(1, p.times.bus - p.busGain + p.boardingPenalty * (added.bus / (baseCounts.bus || 1)));
    const capacity = baseCounts.bus * (1 + p.capacityGrowth / 100);
    const unservedBus = Math.max(0, counts.bus - capacity);
    const busServedFraction = counts.bus ? Math.min(1, capacity / counts.bus) : 1;
    const rows = [];
    function row(key, count, before, after, mode, servedFraction = 1) {
      rows.push({ key, count, served: count * servedFraction, unserved: count * (1 - servedFraction),
        before, after, delta: after - before, mode });
    }
    const nonresident = p.nonresidentShare / 100;
    row('residentDrivers', counts.car * (1 - nonresident), p.times.car, carCommon + p.residentDetour, 'car');
    const purposes = { workDrivers: p.workShare, shoppingDrivers: p.shoppingShare,
      leisureDrivers: p.leisureShare, otherDrivers: 100 - p.workShare - p.shoppingShare - p.leisureShare };
    for (const [key, share] of Object.entries(purposes)) row(key, counts.car * nonresident * share / 100, p.times.car, carCommon + p.visitorDetour, 'car');
    row('existingBus', baseCounts.bus, p.times.bus, busMinutes, 'bus', busServedFraction);
    row('switchBus', added.bus, p.times.car, busMinutes, 'bus', busServedFraction);
    row('switchBicycle', added.bicycle, p.times.car, p.times.bicycle, 'bicycle');
    row('switchWalk', added.walk, p.times.car, p.times.walk, 'walk');
    for (const mode of ['metro', 'train', 'bicycle', 'walk', 'motorcycle', 'other']) row(mode, baseCounts[mode], p.times[mode], p.times[mode], mode);
    const served = rows.reduce((a, r) => a + r.served, 0);
    const beforeMinutes = rows.reduce((a, r) => a + r.count * r.before, 0);
    const afterMinutes = rows.reduce((a, r) => a + r.served * r.after, 0);
    const beforeMean = beforeMinutes / (requests || 1), servedMean = afterMinutes / (served || 1);
    const allServed = unservedBus < 1e-7;
    return { parameters: p, preset, mix, baseCounts, counts, requests, totalDaily, residentDaily,
      shiftedCarTrips: switched, carPressure, estimatedCarsRemoved: switched * p.removalEffect / 100 / p.carOccupancy,
      rows, served, unserved: unservedBus, allServed, beforeMean, servedMean,
      mean: allServed ? servedMean : null,
      meanDelta: allServed ? servedMean - beforeMean : null,
      metroMeanDelta: allServed ? (servedMean - beforeMean) * p.affectedShare / 100 : null,
      personHoursDelta: allServed ? (afterMinutes - beforeMinutes) / 60 : null,
      requiredCapacityGrowth: baseCounts.bus ? Math.max(0, counts.bus / baseCounts.bus - 1) * 100 : null,
      busCapacity: capacity, busMinutes, stageShiftPercent: s * 100,
      caution: 'Conditional accounting with assumed door-to-door times and response curve, not a calibrated metropolitan transport simulation.' };
  }
  function compare(input, facts) {
    const immediate = run(input, facts, 0), future = run(input, facts);
    if (future.error) return future;
    const curve = [];
    for (let s = 0; s <= 60; s++) {
      const r = run(input, facts, s);
      curve.push({ shift: s, mean: r.mean, servedMean: r.servedMean, unserved: r.unserved,
        before: r.beforeMean, remainingDriverDelta: r.rows.find(x => x.key === 'workDrivers').delta });
    }
    const threshold = curve.find(r => r.mean !== null && r.mean < r.before - .000001);
    const countsError = Math.abs(future.rows.reduce((n, r) => n + r.count, 0) - future.requests);
    return { immediate, future, curve, breakEven: threshold?.shift ?? null, countsError };
  }
  root.TravelTransition = { modes, defaults, run, compare, normalize };
})(globalThis);
