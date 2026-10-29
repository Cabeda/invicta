"""Publish the route-first pilot alongside the preserved street experiment."""
from pathlib import Path
import csv, gzip, hashlib, json, math, shutil, statistics, subprocess, zipfile
ROOT=Path(__file__).resolve().parent;LEGACY=ROOT.parent/'costa-cabral';SITE=LEGACY/'proposal'

def publish_line_reference():
    """Publish full geography independently of the native simulation extent."""
    inbound=json.loads((ROOT/'data/official-extension/full-line-service-facts.json').read_text())
    outbound=json.loads((ROOT/'data/official-outbound/full-line-service-facts.json').read_text())
    inbound_shape=json.loads((ROOT/'data/official/inbound_shape.json').read_text())['coordinates']
    metadata=json.loads((ROOT/'data/official/metadata.json').read_text())
    inbound_date=next(row['retrieved_at'] for row in metadata if row['file']=='inbound_shape.json')[:10]
    outbound_date=outbound['geometry_provenance']['retrieved_end_utc'][:10]
    directions={}
    for facts,shape,bundle,retrieved in [(inbound,inbound_shape,'701-extension',inbound_date),(outbound,outbound['shape'],'701-outbound',outbound_date)]:
        direction=str(facts['direction_id'])
        note={'en':f'Official shape retrieved {retrieved}.', 'pt':f'Percurso oficial recolhido em {retrieved}.'}
        if direction=='0':
            note['en']+=' Historical geometry for the 28 October timetable is not verified.'
            note['pt']+=' A geometria histórica para o horário de 28 de outubro não está verificada.'
        directions[direction]={'origin':'Codiceira' if direction=='1' else 'Bolhão', 'destination':facts['destination'],
            'reference_date':facts['reference_date'],'geometry_note':note,'geometry_retrieved':retrieved,'bundle':bundle,
            'stops':facts['stoplist'],'shape':[[p['lng'],p['lat']] for p in sorted(shape,key=lambda p:p['sequence'])],
            'trips':[{k:v for k,v in trip.items() if k in ['trip_id','headsign','stops','originstatus','terminalstatus','stop_time_status','pattern_id']} for trip in facts['trips']],
            'shortcuts':{'areosa':'ARS3' if direction=='1' else 'ARS2','ermesinde':'ERM3' if direction=='1' else 'ERM4'}}
    reference={'schema':'invicta.line-explorer.v1','route':'701','reference_date':inbound['reference_date'],
        'directions':directions,'native':{'direction':'1','from':'ARS3','to':'0BLRB','window':'08:10–08:40'},'operational_direction':'1'}
    (SITE/'701-line-explorer.json').write_text(json.dumps(reference,ensure_ascii=False,separators=(',',':')))
    for name in ['line-explorer.mjs','line-explorer.css']:shutil.copy2(ROOT/name,SITE/name)
    shutil.copytree(ROOT/'data/official-outbound',SITE/'701-outbound',dirs_exist_ok=True)

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
            timed=[b['stops'][i] for b in allb for i,s in enumerate(route['stops']) if s['designated_timing_point']]
            late_calls=sum(c['lateness'] is not None and c['lateness']>0 for c in timed)
            missing_calls=sum(c['lateness'] is None for c in timed)
            early_departures=sum(c.get('departure') is not None and 0<=c['departure']<c['scheduled'] for c in timed)
            short_gaps=0
            for run in runs:
                for i in range(len(route['stops'])):
                    calls=sorted([b['stops'][i] for b in run['buses'] if b['stops'][i]['arrival'] is not None],key=lambda c:c['arrival'])
                    short_gaps+=sum(b['arrival']-a['arrival']<abs(b['scheduled']-a['scheduled'])*.5 for a,b in zip(calls,calls[1:]))
            bycase[case][variant]={'trips':trips,'completed':sum(b['completed'] for b in allb),'planned':len(allb),
                                 'final_lateness':avg([b['final_lateness'] for b in allb]),'generated_delay':avg([b['section_generated_delay'] for b in allb]),'groups':groups,
                                 'timing':{'planned_calls':len(timed),'late_calls':late_calls,'missing_calls':missing_calls,'early_departures':early_departures,
                                           'short_gap_events':short_gaps if all(b['completed'] for b in allb) else None,
                                           'zero_lateness_pass':late_calls==0 and missing_calls==0 and early_departures==0 and short_gaps==0 and all(b['completed'] for b in allb)},
                                 'full_comparison':all(b['completed'] for b in allb)}
    p=route['shape'];bounds=[min(x[0] for x in p),min(x[1] for x in p),max(x[0] for x in p),max(x[1] for x in p)]
    cameras={'corridor':[bounds[0]-180,bounds[1]-180,bounds[2]+180,bounds[3]+180]}
    for key,stop_id in [('areosa','ARS3'),('conde','CF2'),('combatentes','COMB4'),('marques','MPL4'),('fontinha','FTNH2'),('bolhao','0BLRB')]:
        stop=next(s for s in route['stops'] if s['stop_id']==stop_id);x,y=stop['point'];cameras[key]=[x-250,y-250,x+250,y+250]
    for seg in route['segments']:
        a=next(s for s in route['stops'] if s['stop_id']==seg['from']);b=next(s for s in route['stops'] if s['stop_id']==seg['to'])
        seg['shape']=[point for point,length in zip(route['full_shape'],route['shape_lengths']) if a['shape_progress']<=length<=b['shape_progress']]
        seg['shape']=[a['point']]+seg['shape']+[b['point']]
    observations=json.loads((ROOT/'data/observations-summary.json').read_text())
    service_summary=json.loads(subprocess.run(['node',str(ROOT/'service-cli.mjs')],check=True,capture_output=True,text=True).stdout)
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
    for name in ['service-model.mjs','service-panel.mjs']:shutil.copy2(ROOT/name,SITE/name)
    shutil.copy2(ROOT/'data/official-extension/full-line-service-facts.json',SITE/'701-full-service-facts.json')
    shutil.copy2(LEGACY/'inspection-3d.js',SITE/'inspection-3d.js')
    shutil.copytree(LEGACY/'vendor',SITE/'vendor',dirs_exist_ok=True)
    publish_line_reference()
    shutil.copytree(ROOT/'inspection-assets',SITE/'line-701-assets',dirs_exist_ok=True)
    shutil.copytree(ROOT/'data/official',SITE/'701-official',dirs_exist_ok=True)
    shutil.copytree(ROOT/'data/official-extension',SITE/'701-extension',dirs_exist_ok=True)
    public_facts=json.loads((ROOT/'data/source-facts.json').read_text())
    public_facts.update(source_bundle='701-official',metadata_file='701-official/metadata.json')
    public_facts['extension_source_bundle']='701-extension'
    (SITE/'701-source-facts.json').write_text(json.dumps(public_facts,ensure_ascii=False,indent=2))
    shutil.copy2(ROOT/'data/observations-summary.json',SITE/'701-observations.json')
    shutil.copy2(ROOT/'results.json',SITE/'701-experiments.json')
    policy={'route':'701','direction_id':1,'start_stop':route['start'],'end_stop':route['end'],'priority_segments':raw['access']['candidate_priority_segments'],
            'note':'Draft lane permission policy; leaves mapped lane counts, signals and geometry unchanged. Not a street-design approval.'}
    (SITE/'701-policy-template.json').write_text(json.dumps(policy,ensure_ascii=False,indent=2))
    (SITE/'701-observations-template.csv').write_text('trip_id,stop_id,observed_arrival\n')
    report=['# Line 701: full-line exploration and prepared inbound models','', '## Whole-line reference','', 'The explorer shows each direction independently: 56 stops / 63 trips towards Bolhão; 54 stops / 64 trips towards Codiceira or Ermesinde. A continuous focus range and selected trip are retained for each direction in shared links. Short workings retain their unserved stops; no missing departure is invented.', '', 'Timetables refer to 28 October 2026, Europe/Lisbon. Inbound geometry was retrieved on 28 October; outbound geometry was retrieved on 29 October, and its historical applicability to 28 October is not established. The two shapes are independent official references, not one reversed polyline.', '', 'Full-line geography and timetables do not extend native traffic simulation. SUMO and 3D remain inbound Areosa–Bolhão; the separate whole-line delay/queue model remains inbound only. Selecting outbound hides these inbound results. The background map needs internet; route geometry and timetable data are exported with the site.', '', 'Source bundles: `701-extension/metadata.json`, `701-official/metadata.json`, `701-outbound/metadata.json`; combined explorer reference: `701-line-explorer.json`. Outbound: 3,000 uniquely resolved published references, 456 unserved cells and no unresolved matching. See `docs/research/line-701-outbound.md` in the repository for the derivation.', '', '## Prepared Porto street model','',f"Study date: {route['study_date']}. {len(route['stops'])} Porto stops, {route['municipality']['shape_metres']/1000:.3f}km inside the CAOP2025 municipality. Areosa ARS3 is the first stop inside Porto; the municipal entry is about 60m before it. Bolhão 0BLRB is the final stop.",'',
            '## What is known','', 'Current STCP shape, ordered stops and scheduled seconds are frozen with URLs, timestamps and hashes. MPL4 and 0BLRB are designated timing points in Porto. Other calls are intermediate published references. DGT CAOP2025 locates the municipal entry; these are cartographic source positions, not a survey.',
            '',f"Native vehicles start at the mapped municipal entry using an assumed {route['approach_lead_seconds']}s lead before the Areosa reference. There is no official boundary timetable. Reported entry lateness remains measured at Areosa, so it also includes the modeled approach delay. The boundary-crossing edge is excluded from new permission policies to avoid extending restrictions into another municipality.",'',
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
    report+=['','## Simulated Porto street performance','', 'Native SUMO; extended frozen-OSM district, synthetic OD samples including new Marquês–Bolhão demand, fixed 20-second dwell, unverified signals, three seeds and five target 701 trips only. These new outputs supersede the shorter-network results; changed demand/network scope prevents treating differences from the earlier batch as policy gains. The late-entry case adds 180 seconds before municipal entry. Final lateness minus Areosa lateness measures added delay after the first published checkpoint, including intentional timing-point holds. MPL4 and 0BLRB departures wait for their published times. Every unserved request remains visible.','', '| Case | Variant | Completed 701 journeys / planned | Mean final lateness sec (completed only) | Mean unserved all vehicles |','|---|---|---:|---:|---:|']
    for case,variants in bycase.items():
        for variant,stats in variants.items():
            late=stats['final_lateness']['mean'];unserved=sum(g['unserved'] for g in stats['groups'].values())
            report.append(f"| {case} | {variant} | {stats['completed']}/{stats['planned']} | {late:.1f} | {unserved:.1f} |" if late is not None else f"| {case} | {variant} | {stats['completed']}/{stats['planned']} | unavailable | {unserved:.1f} |")
    report+=['','### Native punctuality and spacing checks','', 'These counts cover the five requested native journeys across three seeds. Missing timing-point calls cannot pass the strict check. Arrival-spacing events compare the actual consecutive pair with half its published-time separation; the count is withheld when bus journeys are incomplete. A native timetable pass does not establish sufficient passenger capacity or practical access.',
             '', '| Case | Package | Late timing-point arrivals / planned | Missing calls | Short-gap events | Strict check |','|---|---|---:|---:|---:|---|']
    for case,variants in bycase.items():
        for variant in ['baseline','restricted','all_priority']:
            if variant not in variants:continue
            t=variants[variant]['timing']
            report.append(f"| {case} | {variant} | {t['late_calls']}/{t['planned_calls']} | {t['missing_calls']} | {t['short_gap_events'] if t['short_gap_events'] is not None else 'unavailable'} | {'pass' if t['zero_lateness_pass'] else 'fail'} |")
    report+=['','## Whole-line bunching and cascade checks','', 'A separate operational model covers all 56 stops, 63 inbound workings and 3,024 published calls: 39 start at Codiceira, 24 at Ermesinde. Unserved upstream stops on short workings stay null. All intermediate-reference associations are derived from unique timetable matchings, not raw per-stop trip IDs.',
             '', 'This model uses fluid passenger arrivals, capacity limits, boarding/alighting dwell, single-berth queues and timing-point/headway holding. Running budgets and recovery are assumptions. It simulates one direction with independent vehicles per trip; road traffic outside Porto, other routes, outbound service and shared vehicle rotations are absent. The strict goal is zero late timing-point arrivals, zero early timing-point departures, no gap below half the published spacing, and no passengers left behind. Meeting that goal in a what-if model is not a real-world guarantee.',
             '', 'Default no-shock versus injected-delay scenario:','', '```json',json.dumps(service_summary,ensure_ascii=False,indent=2),'```','',
             'Reduce neither journey counts nor passenger demand to manufacture a punctuality gain. Compare the same demand without the injected delay; secondary changes and short-gap events expose passenger–dwell feedback, while remaining queues expose capacity failures. A late bus can collect more passengers and slow further; a following bus can collect fewer and catch up. Native SUMO separately retains vehicle following and queue spillback within the Porto road network.',
             '', '## Interpretation and next steps','', 'Use the passage-window profile to identify where deviation grows, then collect repeated complete trips before attributing causes. Missing Areosa/Bolhão coverage prevents claiming full-section observed punctuality. A single evening trajectory is an investigative lead, not a causal diagnosis.','',
             'Compare the connectivity-screened package, unrestricted baseline and individual-leg tests. Individual effects must not be added together. Permission-only policies retain identical network geometry and signal programs; a no-change leg is an exact neutral control. Do not rank a policy on faster completed trips when bus or other requests remain unserved.','',
             'Obtain matched full-line AVL and door-open events, boarding/load counts, actual recovery and turnaround times, controller phases, other-line interactions and vehicle/block circulation. Audit lane directions, widths, turns and property/loading access. Calibrate both layers before optimizing for real punctuality or choosing an implementation.','',
             '## Code-first controls','', '`./prototypes/line-701/pilot.sh` rebuilds the route pilot. Export a draft policy JSON from the website, then pass `--scenario /absolute/path/policy.json` to the runner. The static website does not execute new SUMO simulations. The collector and observation importer preserve timestamp/source distinctions.','',
             '## Primary sources','', '- [Official line 701](https://stcp.pt/pt/linhas/701)', '- [STCP route stops API](https://stcp.pt/api/route/701/stops/direction?direction_id=1)', '- [DGT CAOP2025 Porto municipality](https://ogcapi.dgterritorio.gov.pt/collections/municipios/items/1312?f=json)', '- [Porto Digital public bus broker](https://broker.fiware.urbanplatform.portodigital.pt/v2/entities?q=vehicleType%3D%3Dbus&limit=1000)',
             '- Source/API/hash detail: `701-source-facts.json`. Native per-run data: `701-experiments.json`. Observation windows: `701-observations.json`.','']
    (ROOT/'REPORT.md').write_text('\n'.join(report));shutil.copy2(ROOT/'REPORT.md',SITE/'701-report.md')
    (SITE/'README.txt').write_text('INVICTA — LINE 701, CODICEIRA ↔ BOLHÃO\n\nServe this whole folder over HTTP(S). index.html is the bilingual full-line explorer with independent directions and focus sections.\nlegacy.html preserves the earlier Costa Cabral study, population calculator and MP4 films.\nKeep all files, vendor/, inspection-assets/ and line-701-assets/ together.\n3D needs WebGL2 and DecompressionStream. New policies require a local SUMO rerun.\nCurrent official schedules, synthetic native experiments and GPS passage windows are distinct.\nNo calibrated traffic forecast or approved street design is established.\n')
    archive=ROOT/'invicta-line-701-site.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(SITE.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(SITE))
    shutil.copy2(archive,LEGACY/'costa-cabral-proposal-site.zip')
    print('Published route-first pilot:',current,flush=True)
    return public
if __name__=='__main__':build()
