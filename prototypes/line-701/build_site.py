"""Publish the route-first pilot alongside the preserved street experiment."""
from pathlib import Path
import csv, gzip, hashlib, json, math, shutil, statistics, zipfile
ROOT=Path(__file__).resolve().parent;LEGACY=ROOT.parent/'costa-cabral';SITE=LEGACY/'proposal'

def avg(values):
    values=[v for v in values if v is not None]
    return {'mean':statistics.mean(values),'min':min(values),'max':max(values),'n':len(values)} if values else {'mean':None,'min':None,'max':None,'n':0}

def build():
    raw=json.loads((ROOT/'results.json').read_text());route=raw['route'];bycase={}
    for case in raw['meta']['cases']:
        bycase[case]={}
        variants=list(dict.fromkeys(r['variant'] for r in raw['runs'] if r['case']==case))
        for variant in variants:
            runs=[r for r in raw['runs'] if r['case']==case and r['variant']==variant]
            allb=[b for r in runs for b in r['buses']]
            trips={}
            for original in route['morning']:
                buses=[b for b in allb if b['id']==original['id']]
                stops=[]
                for i,stop in enumerate(route['stops']):
                    calls=[b['stops'][i] for b in buses]
                    stops.append({'stop_id':stop['stop_id'],**{key:avg([c.get(key) for c in calls]) for key in ['arrival','departure','lateness','dwell_and_hold']}})
                legs=[]
                for i in range(len(stops)-1):
                    legs.append(avg([b['stops'][i+1]['lateness']-b['stops'][i]['lateness'] for b in buses if b['stops'][i+1]['lateness'] is not None and b['stops'][i]['lateness'] is not None]))
                trips[original['id']]={'stops':stops,'legs':legs,'completed':sum(b['completed'] for b in buses),'planned':len(buses),
                                       'entry_lateness':avg([b['entry_lateness'] for b in buses]),'final_lateness':avg([b['final_lateness'] for b in buses]),
                                       'section_generated_delay':avg([b['section_generated_delay'] for b in buses]),'section_seconds':avg([b['section_seconds'] for b in buses])}
            groups={g:{'planned':statistics.mean(r['groups'][g]['planned'] for r in runs),'unserved':statistics.mean(r['groups'][g]['unserved'] for r in runs),
                       'seconds':avg([r['groups'][g]['mean_duration'] for r in runs])} for g in runs[0]['groups']}
            for g in groups:
                completed=sum(r['groups'][g]['completed'] for r in runs)
                groups[g]['seconds']['mean']=sum((r['groups'][g]['mean_duration'] or 0)*r['groups'][g]['completed'] for r in runs)/completed if completed else None
            bycase[case][variant]={'trips':trips,'completed':sum(b['completed'] for b in allb),'planned':len(allb),
                                 'final_lateness':avg([b['final_lateness'] for b in allb]),'generated_delay':avg([b['section_generated_delay'] for b in allb]),'groups':groups,
                                 'full_comparison':all(b['completed'] for b in allb)}
    p=route['shape'];bounds=[min(x[0] for x in p),min(x[1] for x in p),max(x[0] for x in p),max(x[1] for x in p)]
    cameras={'corridor':[bounds[0]-180,bounds[1]-180,bounds[2]+180,bounds[3]+180]}
    for key,stop_id in [('areosa','ARS3'),('conde','CF2'),('combatentes','COMB4'),('marques','MPL4')]:
        stop=next(s for s in route['stops'] if s['stop_id']==stop_id);x,y=stop['point'];cameras[key]=[x-250,y-250,x+250,y+250]
    for seg in route['segments']:
        a=next(s for s in route['stops'] if s['stop_id']==seg['from']);b=next(s for s in route['stops'] if s['stop_id']==seg['to'])
        seg['shape']=[point for point,length in zip(route['full_shape'],route['shape_lengths']) if a['shape_progress']<=length<=b['shape_progress']]
        seg['shape']=[a['point']]+seg['shape']+[b['point']]
    observations=json.loads((ROOT/'data/observations-summary.json').read_text())
    public={'route':route,'cases':bycase,'access':raw['access'],'geometry':raw['geometry'],'cameras':cameras,'observations':observations,
            'colors':{'bus':'#177455','resident':'#466fba','taxi':'#bb873c','bicycle':'#2e9697','motorcycle':'#87699b','through':'#969b96','background':'#969b96','crossing':'#4a648c'},
            'meta':raw['meta'],'study_midnight':route['study_date']+'T00:00:00+00:00'}
    page=(ROOT/'pilot.template.html').read_text().replace('__LINE701_DATA__',json.dumps(public,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
    SITE.mkdir(exist_ok=True)
    current=SITE/'index.html'
    if current.exists() and 'data-line701="true"' not in current.read_text():
        legacy=current.read_text()
        legacy=legacy.replace('<main>','<main><p class="baseline-disclosure">Arquivo do estudo Costa Cabral / Legacy street experiment. <a href="index.html">Abrir piloto da linha 701 / Open line 701 pilot</a>.</p>',1)
        (SITE/'legacy.html').write_text(legacy)
    current.write_text(page)
    shutil.copy2(ROOT/'pilot.js',SITE/'line-701.js')
    shutil.copy2(LEGACY/'inspection-3d.js',SITE/'inspection-3d.js')
    shutil.copytree(LEGACY/'vendor',SITE/'vendor',dirs_exist_ok=True)
    shutil.copytree(ROOT/'inspection-assets',SITE/'line-701-assets',dirs_exist_ok=True)
    shutil.copytree(ROOT/'data/official',SITE/'701-official',dirs_exist_ok=True)
    public_facts=json.loads((ROOT/'data/source-facts.json').read_text())
    public_facts.update(source_bundle='701-official',metadata_file='701-official/metadata.json')
    (SITE/'701-source-facts.json').write_text(json.dumps(public_facts,ensure_ascii=False,indent=2))
    shutil.copy2(ROOT/'data/observations-summary.json',SITE/'701-observations.json')
    shutil.copy2(ROOT/'results.json',SITE/'701-experiments.json')
    policy={'route':'701','direction_id':1,'start_stop':'ARS3','end_stop':'MPL4','priority_segments':raw['access']['candidate_priority_segments'],
            'note':'Draft lane permission policy; leaves mapped lane counts, signals and geometry unchanged. Not a street-design approval.'}
    (SITE/'701-policy-template.json').write_text(json.dumps(policy,ensure_ascii=False,indent=2))
    (SITE/'701-observations-template.csv').write_text('trip_id,stop_id,observed_arrival\n')
    report=['# Line 701: Areosa → Marquês, inbound towards Bolhão','',f"Study date: {route['study_date']}. Current official route/service snapshot; 13 stops, approximately 3.14km. Ends at MPL4 after the restored MPL7 stop.",'',
            '## What is known','', 'Current STCP route shape, ordered stops and stop schedule seconds are frozen with source URLs, timestamps and hashes. Only MPL4 is a designated timing point within this section. Other stop times are published non-timepoint references. This section does not model the entire 701 line.','',
            '## Observed sample','',f"A bounded evening collection has {observations['counts']['accepted']} unique accepted timestamped positions from {observations['counts']['polls']} polls. Duplicate records are excluded. GPS-derived passage brackets are not door-open arrivals, and this short evening sample does not calibrate morning traffic.",'']
    for trip in observations['trips']:
        if not trip['passages']:continue
        report+=['Trip: '+trip['trip_id'],'','| Stop | Scheduled-reference lateness window (min) |','|---|---:|']
        for passage in trip['passages']:report.append(f"| {passage['stop_id']} | {passage['lateness_low']/60:.2f} … {passage['lateness_high']/60:.2f} |")
        report.append('')
    report+=['## Where general traffic is retained in the candidate','', 'This is a structural screen using generated side-road connector/ordinary-traffic OD pairs, not measured local demand or a legal conclusion. Driveways, loading, emergency access, signage and pedestrian access require field review. Existing exclusive bus lanes are retained; where a new lane is reserved on a multi-lane road, other lanes remain general traffic. Opposite-direction road edges are untouched.','', '| Leg | Section | Newly unreachable generated OD pairs if priority is applied | Decision in candidate |','|---|---|---:|---|']
    for s in route['segments']:
        screen=raw['access']['segments'][s['id']]
        report.append(f"| {s['id']} | {s['from']} → {s['to']} | {screen['newly_unroutable']} | {'priority / existing priority' if s['id'] in policy['priority_segments'] else 'retain general traffic'} |")
    report+=['','## Simulated section performance','', 'Native SUMO; current official timetable; synthetic traffic, fixed 20-second dwell, guessed signals, three seeds, five target 701 trips only. The late-entry case adds an assumed 180 seconds before Areosa. Additional delay in section is final lateness minus actual simulated entry lateness. Intermediate non-timepoint references are not used for holding. MPL4 departures are held to its published time. All unserved requests remain in the accounting.','', '| Case | Variant | Completed 701 journeys / planned | Mean final lateness sec (completed only) | Mean unserved all vehicles |','|---|---|---:|---:|---:|']
    for case,variants in bycase.items():
        for variant,stats in variants.items():
            late=stats['final_lateness']['mean'];unserved=sum(g['unserved'] for g in stats['groups'].values())
            report.append(f"| {case} | {variant} | {stats['completed']}/{stats['planned']} | {late:.1f} | {unserved:.1f} |" if late is not None else f"| {case} | {variant} | {stats['completed']}/{stats['planned']} | unavailable | {unserved:.1f} |")
    report+=['','## Interpretation and next steps','', 'Use the actual passage-window profile to identify where deviation from the published reference grows, then collect repeated complete trips before attributing causes. Missing Areosa coverage means inherited lateness and full-section added observed delay cannot be separated for that trip. A single-trip evening increase is a lead for investigation, not proof that car traffic, signals or boarding caused it.','',
             'Compare an access-preserving package, unrestricted baseline and individual-leg tests. Individual effects must not be added together. Permission-only policies retain identical network geometry and signal programs; a no-change leg is an exact neutral control. Do not rank a policy on faster completed trips when bus or other requests remain unserved.','',
             'Map-match and audit the actual bus turns, widths, stop locations, signal phases and loading/property access; obtain a matched AVL/door-open/history dataset and target-route passenger loads. Include other bus lines in subsequent network validation. Extend to the full 701 line after this direction and section are validated.','',
             '## Code-first controls','', '`./prototypes/line-701/pilot.sh` rebuilds the route pilot. Export a draft policy JSON from the website, then pass `--scenario /absolute/path/policy.json` to the runner. The static website does not execute new SUMO simulations. The collector and observation importer preserve timestamp/source distinctions.','',
             '## Primary sources','', '- [Official line 701](https://stcp.pt/pt/linhas/701)', '- [STCP route stops API](https://stcp.pt/api/route/701/stops/direction?direction_id=1)', '- [Porto Digital public bus broker](https://broker.fiware.urbanplatform.portodigital.pt/v2/entities?q=vehicleType%3D%3Dbus&limit=1000)',
             '- Source/API/hash detail: `701-source-facts.json`. Native per-run data: `701-experiments.json`. Observation windows: `701-observations.json`.','']
    (ROOT/'REPORT.md').write_text('\n'.join(report));shutil.copy2(ROOT/'REPORT.md',SITE/'701-report.md')
    (SITE/'README.txt').write_text('INVICTA — LINE 701, AREOSA → MARQUÊS\n\nServe this whole folder over HTTP(S). index.html is the route-first bilingual pilot.\nlegacy.html preserves the earlier Costa Cabral study, population calculator and MP4 films.\nKeep all files, vendor/, inspection-assets/ and line-701-assets/ together.\n3D needs WebGL2 and DecompressionStream. New policies require a local SUMO rerun.\nCurrent official schedules, synthetic native experiments and GPS passage windows are distinct.\nNo calibrated traffic forecast or approved street design is established.\n')
    archive=ROOT/'invicta-line-701-site.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(SITE.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(SITE))
    shutil.copy2(archive,LEGACY/'costa-cabral-proposal-site.zip')
    print('Published route-first pilot:',current,flush=True)
    return public
if __name__=='__main__':build()
