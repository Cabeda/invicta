// THROWAWAY inspection layer. SUMO owns movement; this module only displays it.
import * as T from './vendor/three.module.js';
import { OrbitControls } from './vendor/OrbitControls.js';

async function readAsset(name, assetBase = './inspection-assets/') {
  const response = await fetch(new URL(`${assetBase}${name}.json.gz`, import.meta.url));
  if (!response.ok) throw new Error(`Missing inspection asset: ${name}`);
  const stream = response.body.pipeThrough(new DecompressionStream('gzip'));
  return new Response(stream).json();
}

export async function createInspection({ data, getState, label, changed, assetBase = './inspection-assets/' }) {
  const source = await readAsset('scene', assetBase);
  const mid = data.cameras.corridor;
  const origin = [(mid[0] + mid[2]) / 2, (mid[1] + mid[3]) / 2];
  const world = (x, y, h = 0) => new T.Vector3(x - origin[0], h, origin[1] - y);
  const cache = new Map(), panels = {}, unit = new T.BoxGeometry(1, 1, 1);
  const dummy = new T.Object3D(), frustum = new T.Frustum(), viewMatrix = new T.Matrix4();
  const laneMap = new Map(source.lanes.map(l => [l.id, l]));
  const distance = new Map();
  let caseKey = '', loading = false, generation = 0, active = false, steering = false;
  let cameraKey = '', lastTime = 0, drag = null, movementSerial = 0;
  const keys = new Set();

  for (const lane of source.lanes) {
    const cumulative = [0];
    for (let i = 1; i < lane.shape.length; i++) {
      cumulative.push(cumulative[i - 1] + Math.hypot(lane.shape[i][0] - lane.shape[i - 1][0], lane.shape[i][1] - lane.shape[i - 1][1]));
    }
    distance.set(lane.id, cumulative);
  }

  function atLane(laneIndex, position) {
    const lane = source.lanes[laneIndex], cumulative = lane && distance.get(lane.id);
    if (!lane || !cumulative || !lane.length) return null;
    const d = Math.max(0, Math.min(cumulative.at(-1), position * cumulative.at(-1) / lane.length));
    let i = 1;
    while (i < cumulative.length - 1 && cumulative[i] < d) i++;
    const a = lane.shape[i - 1], b = lane.shape[i];
    if (!b) return null;
    const f = (d - cumulative[i - 1]) / (cumulative[i] - cumulative[i - 1] || 1);
    return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, (Math.atan2(b[0] - a[0], b[1] - a[1]) * 180 / Math.PI + 360) % 360];
  }

  // Interpolate distance on a lane when possible; use native positions at changes.
  function positions(replay, time) {
    const i = Math.max(0, Math.min(replay.frames.length - 1, Math.floor(time - replay.start)));
    const a = replay.frames[i], b = replay.frames[Math.min(i + 1, replay.frames.length - 1)];
    const f = Math.max(0, Math.min(1, time - a.t)), next = new Map(b.vehicles.map(v => [v[0], v]));
    return a.vehicles.map(row => {
      const n = next.get(row[0]) || row;
      const onLane = row[5] === n[5] ? atLane(row[5], row[6] + (n[6] - row[6]) * f) : null;
      return { index: row[0], id: replay.vehicles[row[0]].id, group: replay.vehicles[row[0]].group,
        x: onLane ? onLane[0] : row[1] + (n[1] - row[1]) * f,
        y: onLane ? onLane[1] : row[2] + (n[2] - row[2]) * f,
        angle: onLane ? onLane[2] : row[3] + (((n[3] - row[3] + 540) % 360) - 180) * f,
        speed: row[4], lane: row[5] };
    });
  }

  function geometry(vertices, normals) {
    const g = new T.BufferGeometry();
    g.setAttribute('position', new T.Float32BufferAttribute(vertices, 3));
    if (normals) g.setAttribute('normal', new T.Float32BufferAttribute(normals, 3)); else g.computeVertexNormals();
    g.computeBoundingSphere();
    return g;
  }

  function ribbons(lanes, widthFor, height) {
    const vertices = [];
    for (const lane of lanes) {
      const width = widthFor(lane), points = lane.shape;
      for (let i = 1; i < points.length; i++) {
        const a = world(...points[i - 1], height), b = world(...points[i], height);
        const dx = b.x - a.x, dz = b.z - a.z, d = Math.hypot(dx, dz);
        if (!d) continue;
        const nx = -dz / d * width / 2, nz = dx / d * width / 2;
        const p = [a.x + nx, height, a.z + nz], q = [a.x - nx, height, a.z - nz];
        const r = [b.x + nx, height, b.z + nz], s = [b.x - nx, height, b.z - nz];
        vertices.push(...p, ...q, ...r, ...q, ...s, ...r);
      }
    }
    return geometry(vertices);
  }

  function surfaces(polygons, height) {
    const vertices = [];
    for (const polygon of polygons) {
      const contour = polygon.map(p => new T.Vector2(p[0] - origin[0], origin[1] - p[1]));
      for (const triangle of T.ShapeUtils.triangulateShape(contour, [])) {
        for (const i of triangle) vertices.push(contour[i].x, height, contour[i].y);
      }
    }
    return geometry(vertices);
  }

  const corridor = source.lanes.filter(l => !l.internal && l.corridor && l.policy === 'restricted');
  const policyGeometry = {};
  for (const policy of ['baseline', 'restricted']) {
    const external = source.lanes.filter(l => !l.internal && l.policy === policy);
    const highlighted = l => source.show_lane_permissions ? l.corridor && l.bus_priority : l.corridor;
    const general = external.filter(l => !highlighted(l)), local = external.filter(highlighted);
    policyGeometry[policy] = { road: ribbons(general, l => l.width, .025), corridor: ribbons(local, l => l.width, .035),
      junction: surfaces(source.junctions[policy], .02), guide: ribbons(local, () => .07, .045) };
  }
  const buildingVertices = [], buildingNormals = [];
  for (const building of source.buildings.features) {
    const shape = new T.Shape(building.shape.map(p => new T.Vector2(p[0] - origin[0], p[1] - origin[1])));
    const g = new T.ExtrudeGeometry(shape, { depth: building.height, bevelEnabled: false, steps: 1 });
    g.rotateX(-Math.PI / 2);
    buildingVertices.push(...g.attributes.position.array);
    buildingNormals.push(...g.attributes.normal.array);
    g.dispose();
  }
  const buildingGeometry = geometry(buildingVertices, buildingNormals);
  const buildingOutline = new T.EdgesGeometry(buildingGeometry, 25);
  const roadMaterial = new T.MeshBasicMaterial({ color: '#717c7d', side: T.DoubleSide });
  const junctionMaterial = new T.MeshBasicMaterial({ color: '#717c7d', side: T.DoubleSide });
  const buildingsMaterial = new T.MeshLambertMaterial({ color: '#e1d5bb' });

  function createPanel(policy) {
    const host = document.getElementById(`${policy}3D`);
    const renderer = new T.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true, logarithmicDepthBuffer: true });
    renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 1.5));
    renderer.outputColorSpace = T.SRGBColorSpace;
    renderer.toneMapping = T.ACESFilmicToneMapping;
    renderer.toneMappingExposure = .9;
    renderer.domElement.tabIndex = 0;
    renderer.domElement.setAttribute('aria-label', label('threeCanvas'));
    host.append(renderer.domElement);
    const scene = new T.Scene();
    scene.background = new T.Color('#dce8ec');
    scene.fog = new T.Fog('#dce8ec', 850, 3500);
    scene.add(new T.HemisphereLight('#ffffff', '#8b927e', 1.7));
    const sun = new T.DirectionalLight('#fff1d9', 1.6); sun.position.set(-300, 600, 180); scene.add(sun);
    const ground = new T.Mesh(new T.PlaneGeometry(18000, 18000), new T.MeshLambertMaterial({ color: '#c8d2bf' }));
    ground.rotation.x = -Math.PI / 2; ground.position.y = -.05; scene.add(ground);
    const mesh = policyGeometry[policy];
    scene.add(new T.Mesh(mesh.road, roadMaterial), new T.Mesh(mesh.junction, junctionMaterial));
    scene.add(new T.Mesh(mesh.corridor, new T.MeshBasicMaterial({ color: policy === 'restricted' ? '#4d826b' : '#667574', side: T.DoubleSide })));
    scene.add(new T.Mesh(mesh.guide, new T.MeshBasicMaterial({ color: '#c7ddd0', side: T.DoubleSide })));
    const buildings = new T.Group();
    buildings.add(new T.Mesh(buildingGeometry, buildingsMaterial));
    buildings.add(new T.LineSegments(buildingOutline, new T.LineBasicMaterial({ color: '#a89c87', transparent: true, opacity: .32 })));
    scene.add(buildings);
    const stopMaterial = new T.MeshBasicMaterial({ color: '#2d657e' });
    for (const stop of source.stops.filter(s => s.policy === policy)) {
      const lane = laneMap.get(stop.lane), p = atLane(source.lanes.indexOf(lane), stop.pos);
      if (!p) continue;
      const r = p[2] * Math.PI / 180, offset = lane.width / 2 + .5;
      const pos = world(p[0] + Math.cos(r) * offset, p[1] - Math.sin(r) * offset);
      const pole = new T.Mesh(new T.CylinderGeometry(.05, .05, 2.5, 6), stopMaterial);
      pole.position.copy(pos); pole.position.y = 1.25;
      const sign = new T.Mesh(new T.BoxGeometry(.55, .55, .08), stopMaterial);
      sign.position.copy(pos); sign.position.y = 2.35;
      scene.add(pole, sign);
    }
    const camera = new T.PerspectiveCamera(48, 1, .15, 16000);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = false; controls.minDistance = 5; controls.maxDistance = 6000;
    controls.maxPolarAngle = Math.PI / 2 - .01;
    const marker = new T.Mesh(new T.TorusGeometry(4.2, .16, 6, 40), new T.MeshBasicMaterial({ color: '#f5bb44' }));
    marker.rotation.x = Math.PI / 2; marker.visible = false; scene.add(marker);
    const models = {};
    for (const [group, dim] of Object.entries(source.vehicle_dimensions.types)) {
      const material = new T.MeshLambertMaterial({ color: data.colors[group] || '#929b96' });
      const body = new T.InstancedMesh(unit, material, 2500);
      const window = new T.InstancedMesh(unit, new T.MeshLambertMaterial({ color: '#263e49' }), 2500);
      const wheelVertices = [], wheelNormals = [], radius = Math.min(.38, dim.height * .23);
      for (const side of [-1, 1]) for (const end of [-1, 1]) {
        const g = new T.CylinderGeometry(radius, radius, .16, 10).toNonIndexed();
        g.rotateZ(Math.PI / 2); g.translate(side * (dim.width / 2 - .06), radius, end * dim.length * .32);
        wheelVertices.push(...g.attributes.position.array); wheelNormals.push(...g.attributes.normal.array); g.dispose();
      }
      const wheels = new T.InstancedMesh(geometry(wheelVertices, wheelNormals), new T.MeshLambertMaterial({ color: '#172b2b' }), 2500);
      for (const mesh of [body, window, wheels]) { mesh.instanceMatrix.setUsage(T.DynamicDrawUsage); mesh.frustumCulled = false; }
      scene.add(body, window, wheels); models[group] = { body, window, wheels, dim };
    }
    const panel = { policy, host, renderer, scene, camera, controls, buildings, models, marker, rows: [], yaw: 0, pitch: -.04 };
    controls.addEventListener('change', () => {
      if (steering || getState().perspective !== 'orbit') return;
      steering = true;
      for (const other of Object.values(panels)) {
        if (other === panel) continue;
        other.camera.position.copy(camera.position); other.controls.target.copy(controls.target); other.controls.update();
      }
      steering = false;
      render();
    });
    renderer.domElement.addEventListener('pointerdown', e => {
      renderer.domElement.focus({ preventScroll: true });
      if (getState().perspective !== 'street') return;
      drag = { panel, x: e.clientX, y: e.clientY };
      renderer.domElement.setPointerCapture(e.pointerId);
    });
    renderer.domElement.addEventListener('pointermove', e => {
      if (!drag || drag.panel !== panel) return;
      panel.yaw -= (e.clientX - drag.x) * .004; panel.pitch = Math.max(-1.2, Math.min(1.1, panel.pitch - (e.clientY - drag.y) * .004));
      drag.x = e.clientX; drag.y = e.clientY;
      for (const other of Object.values(panels)) { other.yaw = panel.yaw; other.pitch = panel.pitch; }
      render();
    });
    const release = () => { drag = null; };
    renderer.domElement.addEventListener('pointerup', release);
    renderer.domElement.addEventListener('pointercancel', release);
    return panel;
  }

  try {
    for (const policy of ['baseline', 'restricted']) panels[policy] = createPanel(policy);
  } catch (error) {
    for (const panel of Object.values(panels)) { panel.renderer.dispose(); panel.host.replaceChildren(); }
    throw error;
  }

  function resetCamera() {
    const state = getState(), box = data.cameras[state.camera];
    const centre = world((box[0] + box[2]) / 2, (box[1] + box[3]) / 2);
    const width = state.camera === 'corridor' ? Math.max(box[2] - box[0], box[3] - box[1]) : 280;
    // Put street-level inspection on the nearest modelled corridor lane.
    let nearest = null, best = Infinity;
    for (const lane of corridor) for (const p of lane.shape) {
      const d = Math.hypot(p[0] - (box[0] + box[2]) / 2, p[1] - (box[1] + box[3]) / 2);
      if (d < best) { nearest = p; best = d; }
    }
    steering = true;
    for (const panel of Object.values(panels)) {
      panel.controls.enabled = state.perspective === 'orbit';
      if (state.perspective === 'street') {
        panel.camera.position.copy(world(...nearest, 1.7)); panel.yaw = .35; panel.pitch = -.03;
      } else {
        panel.camera.position.copy(centre).add(new T.Vector3(width * .45, width * .55, width * .6));
        panel.controls.target.copy(centre); panel.controls.update();
      }
    }
    steering = false;
  }

  function pointCamera(panel) {
    panel.camera.lookAt(panel.camera.position.clone().add(new T.Vector3(Math.sin(panel.yaw) * Math.cos(panel.pitch), Math.sin(panel.pitch), -Math.cos(panel.yaw) * Math.cos(panel.pitch))));
  }

  function matrix(mesh, index, row, dim, window) {
    const angle = row.angle * Math.PI / 180;
    const centre = world(row.x - Math.sin(angle) * dim.length / 2, row.y - Math.cos(angle) * dim.length / 2);
    dummy.position.copy(centre);
    dummy.position.y = window === 'wheels' ? 0 : window ? dim.height * .70 : dim.height / 2;
    dummy.rotation.set(0, -angle, 0);
    if (window === 'wheels') dummy.scale.set(1, 1, 1);
    else dummy.scale.set(dim.width * (window ? 1.006 : 1), dim.height * (window ? .26 : 1), dim.length * (window ? 1.006 : 1));
    dummy.updateMatrix(); mesh.setMatrixAt(index, dummy.matrix);
  }

  function render() {
    if (!active || loading) return;
    const state = getState(), following = state.perspective === 'follow';
    const messages = [];
    for (const panel of Object.values(panels)) {
      if (state.view !== 'compare' && state.view !== panel.policy) continue;
      const rect = panel.host.getBoundingClientRect();
      if (!rect.width || !rect.height) continue;
      panel.renderer.setSize(rect.width, rect.height, false);
      panel.camera.aspect = rect.width / rect.height; panel.camera.updateProjectionMatrix();
      panel.buildings.visible = state.buildings;
      const replay = cache.get(`${state.case}-${panel.policy}`);
      if (!replay) continue;
      panel.rows = positions(replay, state.time);
      const bus = panel.rows.find(r => r.id === state.follow);
      if (following && bus) {
        const dim = source.vehicle_dimensions.types.bus, r = bus.angle * Math.PI / 180;
        const centre = world(bus.x - Math.sin(r) * dim.length / 2, bus.y - Math.cos(r) * dim.length / 2);
        panel.camera.position.copy(centre).add(new T.Vector3(-Math.sin(r) * 16, 7, Math.cos(r) * 16));
        panel.camera.lookAt(centre.clone().add(new T.Vector3(Math.sin(r) * 9, 1.8, -Math.cos(r) * 9)));
        panel.marker.position.copy(centre); panel.marker.position.y = .12; panel.marker.visible = true;
        messages.push(`${label(panel.policy)}: ${bus.id} · ${Math.round(bus.speed * 3.6)} km/h`);
      } else {
        panel.marker.visible = false;
        if (following) messages.push(`${label(panel.policy)}: ${label('busInactive')}`);
      }
      if (state.perspective === 'street') pointCamera(panel);
      panel.camera.updateMatrixWorld();
      viewMatrix.multiplyMatrices(panel.camera.projectionMatrix, panel.camera.matrixWorldInverse);
      frustum.setFromProjectionMatrix(viewMatrix);
      const counts = Object.fromEntries(Object.keys(panel.models).map(k => [k, 0]));
      let visible = 0;
      for (const row of panel.rows) {
        const model = panel.models[row.group]; if (!model) continue;
        const index = counts[row.group]++;
        matrix(model.body, index, row, model.dim, false); matrix(model.window, index, row, model.dim, true); matrix(model.wheels, index, row, model.dim, 'wheels');
        if (frustum.containsPoint(world(row.x, row.y, .8))) visible++;
      }
      for (const [group, model] of Object.entries(panel.models)) {
        model.body.count = model.window.count = model.wheels.count = counts[group];
        model.body.instanceMatrix.needsUpdate = model.window.instanceMatrix.needsUpdate = model.wheels.instanceMatrix.needsUpdate = true;
      }
      panel.renderer.render(panel.scene, panel.camera);
      document.getElementById(`${panel.policy}Counter`).textContent = `${visible} ${label('visible')}`;
    }
    document.getElementById('threeState').textContent = messages.length ? messages.join(' · ') : label(state.perspective === 'street' ? 'streetHelp' : 'orbitHelp');
  }

  async function loadCase() {
    const current = getState().case;
    if (caseKey === current && !loading) return;
    const token = ++generation;
    loading = true;
    document.getElementById('threeState').textContent = label('threeLoading');
    await Promise.all(['baseline', 'restricted'].map(async policy => {
      const key = `${current}-${policy}`;
      if (!cache.has(key)) cache.set(key, await readAsset(key, assetBase));
    }));
    if (token !== generation) return;
    caseKey = current; loading = false;
    const select = document.getElementById('followBus');
    const ids = new Set(['baseline', 'restricted'].flatMap(policy => cache.get(`${current}-${policy}`).vehicles.filter(v => v.group === 'bus').map(v => v.id)));
    select.replaceChildren(...[...ids].sort((a, b) => Number(a.split('_')[1]) - Number(b.split('_')[1])).map(id => {
      const option = document.createElement('option'); option.value = id;
      option.textContent = `${source.bus_info[id]?.line || ''} · ${id}`; return option;
    }));
    if (!ids.has(getState().follow)) chooseBus();
    select.value = getState().follow;
    render();
  }

  function chooseBus() {
    const state = getState(), replay = cache.get(`${state.case}-restricted`);
    if (!replay) return;
    const box = data.cameras[state.camera], x = (box[0] + box[2]) / 2, y = (box[1] + box[3]) / 2;
    const available = positions(replay, state.time).filter(v => v.group === 'bus');
    available.sort((a, b) => Math.hypot(a.x - x, a.y - y) - Math.hypot(b.x - x, b.y - y));
    if (available.length) state.follow = available[0].id;
    else state.follow = replay.vehicles.find(v => v.group === 'bus')?.id || '';
  }

  const canMove = () => active && ['orbit', 'street'].includes(getState().perspective);
  const isCanvas = target => Object.values(panels).some(p => p.renderer.domElement === target);
  function movementSpeed() {
    const p = panels.restricted;
    const base = getState().perspective === 'orbit' ? T.MathUtils.clamp(p.camera.position.distanceTo(p.controls.target) * .12, 12, 180) : 5;
    return base * (getState().cameraSpeed ?? 1);
  }
  function movement(forward, right, metres = movementSpeed() * .25) {
    if (!canMove() || (!forward && !right) || !metres) return;
    const reference = panels.restricted, heading = new T.Vector3();
    if (getState().perspective === 'orbit') {
      reference.camera.getWorldDirection(heading); heading.y = 0;
      // At a top-down angle, use screen-up rather than an unstable horizontal heading.
      if (heading.lengthSq() < 1e-6) { heading.set(0, 1, 0).applyQuaternion(reference.camera.quaternion); heading.y = 0; }
      heading.normalize();
    } else heading.set(Math.sin(reference.yaw), 0, -Math.cos(reference.yaw));
    const delta = heading.clone().multiplyScalar(forward).add(new T.Vector3(-heading.z, 0, heading.x).multiplyScalar(right));
    if (delta.lengthSq() > 1) delta.normalize();
    delta.multiplyScalar(metres);
    steering = true;
    for (const panel of Object.values(panels)) {
      panel.camera.position.add(delta);
      if (getState().perspective === 'orbit') { panel.controls.target.add(delta); panel.controls.update(); }
    }
    steering = false; movementSerial++;
    render();
  }

  const allowedKeys = new Set(['w', 'a', 's', 'd', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright']);
  window.addEventListener('keydown', e => {
    if (!canMove() || !isCanvas(e.target) || (!allowedKeys.has(e.key.toLowerCase()) && e.key !== 'Shift')) return;
    e.preventDefault(); keys.add(e.key.toLowerCase());
  });
  window.addEventListener('keyup', e => keys.delete(e.key.toLowerCase()));
  window.addEventListener('blur', () => keys.clear());
  window.addEventListener('focusin', e => { if (!isCanvas(e.target)) keys.clear(); });
  document.addEventListener('visibilitychange', () => { if (document.hidden) keys.clear(); });
  for (const button of document.querySelectorAll('[data-walk]')) {
    let pressSerial = null;
    const step = () => movement(button.dataset.walk === 'w' ? 1 : button.dataset.walk === 's' ? -1 : 0,
      button.dataset.walk === 'd' ? 1 : button.dataset.walk === 'a' ? -1 : 0);
    button.addEventListener('pointerdown', e => { if (!canMove()) return; e.preventDefault(); pressSerial = movementSerial; keys.add(button.dataset.walk); button.setPointerCapture(e.pointerId); });
    for (const event of ['pointerup', 'pointercancel', 'lostpointercapture']) button.addEventListener(event, () => keys.delete(button.dataset.walk));
    // A quick tap can fall between animation frames; keyboard activation also needs a step.
    button.addEventListener('click', e => { if (e.detail === 0 || movementSerial === pressSerial) step(); pressSerial = null; });
  }
  function animate(now) {
    const dt = lastTime ? Math.min((now - lastTime) / 1000, .1) : 0; lastTime = now;
    if (keys.size && active) {
      const pressed = (...options) => options.some(k => keys.has(k)) ? 1 : 0;
      movement(pressed('w', 'arrowup') - pressed('s', 'arrowdown'), pressed('d', 'arrowright') - pressed('a', 'arrowleft'), dt * movementSpeed() * (keys.has('shift') ? 4 : 1));
    }
    requestAnimationFrame(animate);
  }
  requestAnimationFrame(animate);

  return {
    async update() {
      active = getState().dimension === '3d';
      for (const panel of Object.values(panels)) panel.controls.panSpeed = getState().cameraSpeed ?? 1;
      for (const button of document.querySelectorAll('[data-walk]')) button.disabled = !canMove();
      if (!active) { keys.clear(); return; }
      const state = getState(), key = `${state.camera}-${state.perspective}`;
      if (key !== cameraKey) { keys.clear(); cameraKey = key; resetCamera(); }
      await loadCase(); render();
    },
    draw: render,
    canvas(policy) { return panels[policy].renderer.domElement; },
    reset() { resetCamera(); render(); },
    selectBus(id) {
      const state = getState(); state.follow = id;
      const replay = cache.get(`${state.case}-restricted`), index = replay?.vehicles.findIndex(v => v.id === id);
      if (index >= 0 && !positions(replay, state.time).some(v => v.id === id)) {
        const first = replay.frames.find(f => f.vehicles.some(v => v[0] === index)); if (first) state.time = first.t;
      }
      changed(); render();
    },
    followNearest() { chooseBus(); document.getElementById('followBus').value = getState().follow; render(); },
    pose() { const p = panels.restricted; return { position: p.camera.position.toArray(), target: p.controls.target.toArray(), yaw: p.yaw, pitch: p.pitch }; },
    restore(pose) {
      if (!pose || !Array.isArray(pose.position) || !Array.isArray(pose.target) || pose.position.length !== 3 || pose.target.length !== 3 || ![...pose.position, ...pose.target, pose.yaw, pose.pitch].every(Number.isFinite)) return;
      steering = true;
      for (const panel of Object.values(panels)) {
        panel.camera.position.fromArray(pose.position); panel.controls.target.fromArray(pose.target);
        panel.yaw = pose.yaw; panel.pitch = pose.pitch; if (getState().perspective === 'orbit') panel.controls.update();
      }
      steering = false; render();
    },
    debug() { return { loaded: !loading, case: caseKey, buildings: source.buildings.features.length, lanes: source.lanes.length, vehicles: Object.fromEntries(Object.entries(panels).map(([k, p]) => [k, p.rows.length])), network: source.network_sha256,
      cameras: Object.fromEntries(Object.entries(panels).map(([k,p]) => [k,{position:p.camera.position.toArray(),target:p.controls.target.toArray()}])) }; }
  };
}
