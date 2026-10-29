"""Publish direction-specific views of the same bidirectional native traffic runs."""
from pathlib import Path
import json,statistics,shutil
import sys
ROOT=Path(__file__).resolve().parent;PILOT=ROOT.parent
sys.path.insert(0,str(ROOT))
from publication import validate_publication,digest

def avg(values):
    values=[v for v in values if v is not None]
    return {'mean':statistics.mean(values),'min':min(values),'max':max(values),'n':len(values)} if values else {'mean':None,'min':None,'max':None,'n':0}
def clock(value):
    if value is None:return '—'
    return f'{int(value)//3600:02}:{int(value)%3600//60:02}:{int(value)%60:02}'

def publish(site,original_observations):
    results_file=ROOT/'results.json';manifest_file=ROOT/'inspection-assets/manifest.json'
    if not results_file.exists() or not manifest_file.exists():return None
    raw=json.loads(results_file.read_text());reference=raw['route_reference'];manifest=json.loads(manifest_file.read_text());validate_publication(ROOT,raw,manifest)
    directions={};screens=raw['access'];change_lookup={c['edge']:c for c in screens['changes']};potential_lookup={c['edge']:c for c in screens['changes']+screens['general_traffic_retained']}
    masks={};route_ui={}
    for direction,route in reference['directions'].items():
        segments=[];owned=set()
        for i,(a,b) in enumerate(zip(route['stops'],route['stops'][1:])):
            edges=route['path'][a['path_index']:b['path_index']+1];new=[e for e in edges if e not in owned];owned.update(new)
            points=[p for p,l in zip(route['shape'],route['shape_lengths']) if a['shape_progress']<=l<=b['shape_progress']]
            segments.append({'id':f'leg_{i+1:02}','index':i,'from':a['stop_id'],'to':b['stop_id'],'from_name':a['stop_name'],'to_name':b['stop_name'],'edges':new,'route_edges':edges,'shape':[a['point']]+points+[b['point']],
                'shape_metres':b['shape_progress']-a['shape_progress'],'streets':list(dict.fromkeys(g['name'] for g in raw['geometry'] if g['id'] in edges))})
        masks[direction]=[s['id'] for s in segments if any(e in change_lookup for e in s['edges'])]
        route_ui[direction]=segments
    policy_masks={'baseline':{d:[] for d in masks},'restricted':masks,'all_priority':{d:[s['id'] for s in segments] for d,segments in route_ui.items()}}
    for direction,route in reference['directions'].items():
        segments=route_ui[direction];bycase={};morning=[]
        for trip in route['trips']:
            lookup={s['stop_id']:s for s in trip['stops']}
            morning.append({**trip,'origin':trip['stops'][0]['stop_id'],'destination':trip['stops'][-1]['stop_id'],
                'stops':[{**s,'scheduled':lookup.get(s['stop_id'],{}).get('scheduled'),'scheduled_text':clock(lookup.get(s['stop_id'],{}).get('scheduled'))} for s in route['stops']]})
        for case in raw['meta']['cases']:
            bycase[case]={}
            for variant in ['baseline','restricted']:
                runs=[r for r in raw['runs'] if r['case']==case and r['variant']==variant];buses=[b for r in runs for b in r['buses'] if b['direction']==direction];trips={}
                for trip in morning:
                    actual=[b for b in buses if b['id']==trip['id']];stops=[]
                    for s in route['stops']:
                        calls=[next((c for c in b['stops'] if c['stop_id']==s['stop_id']),{}) for b in actual]
                        stops.append({'stop_id':s['stop_id'],**{key:avg([c.get(key) for c in calls]) for key in ['arrival','departure','lateness','dwell_and_hold']}})
                    trips[trip['id']]={'stops':stops,'completed':sum(b['completed'] for b in actual),'planned':len(actual),**{key:avg([b[key] for b in actual]) for key in ['entry_lateness','final_lateness','section_generated_delay','section_seconds']}}
                groups={}
                for group in runs[0]['groups']:
                    rows=[r['groups'][group] for r in runs];completed=sum(g['completed'] for g in rows)
                    groups[group]={'planned':statistics.mean(g['planned'] for g in rows),'unserved':statistics.mean(g['unserved'] for g in rows),'seconds':avg([g['mean_duration'] for g in rows])}
                    groups[group]['seconds']['mean']=sum((g['mean_duration'] or 0)*g['completed'] for g in rows)/completed if completed else None
                    groups[group]['departure_delay']={'mean':sum((g['mean_depart_delay'] or 0)*g['completed'] for g in rows)/completed if completed else None,'n':completed}
                timing_ids={s['stop_id'] for s in route['stops'] if s['designated_timing_point']};timed=[c for b in buses for c in b['stops'] if c['stop_id'] in timing_ids];late=sum(c['lateness'] is not None and c['lateness']>0 for c in timed);missing=sum(c['arrival'] is None for c in timed);early=sum(c['departure'] is not None and 0<=c['departure']<c['scheduled'] for c in timed)
                gaps=0
                for run in runs:
                    for stop in route['stops']:
                        calls=sorted([c for b in run['buses'] if b['direction']==direction for c in b['stops'] if c['stop_id']==stop['stop_id'] and c['arrival'] is not None],key=lambda c:c['arrival'])
                        gaps+=sum(b['arrival']-a['arrival']<abs(b['scheduled']-a['scheduled'])*.5 for a,b in zip(calls,calls[1:]))
                complete=all(b['completed'] for b in buses)
                bycase[case][variant]={'trips':trips,'completed':sum(b['completed'] for b in buses),'planned':len(buses),'groups':groups,'final_lateness':avg([b['final_lateness'] for b in buses]),'generated_delay':avg([b['section_generated_delay'] for b in buses]),
                    'timing':{'planned_calls':len(timed),'late_calls':late,'missing_calls':missing,'early_departures':early,'short_gap_events':gaps if complete else None,'zero_lateness_pass':late==0 and missing==0 and early==0 and gaps==0 and complete},'full_comparison':complete}
        cameras={'corridor':[min(p[0] for p in route['shape'])-200,min(p[1] for p in route['shape'])-200,max(p[0] for p in route['shape'])+200,max(p[1] for p in route['shape'])+200]};labels={'corridor':'Linha inteira / Whole line'}
        stops={s['stop_id']:s for s in route['stops']}
        locations=[('codiceira','COD4'),('ermesinde','ERM3' if direction=='1' else 'ERM4'),('alto','AM2' if direction=='1' else 'AM1'),('areosa','ARS3' if direction=='1' else 'ARS2'),('conde','CF2' if direction=='1' else 'CF1'),('combatentes','COMB4' if direction=='1' else 'COMB1'),('marques','MPL4' if direction=='1' else 'MPL2'),('fontinha','FTNH2' if direction=='1' else 'FTNH1'),('bolhao','0BLRB' if direction=='1' else 'BLRB3')]
        for key,ident in locations:
            if ident in stops:x,y=stops[ident]['point'];cameras[key]=[x-250,y-250,x+250,y+250];labels[key]=stops[ident]['stop_name']
        facts=json.loads((PILOT/('data/official-extension/full-line-service-facts.json' if direction=='1' else 'data/official-outbound/full-line-service-facts.json')).read_text())
        observations={**original_observations,'timetables':{t['trip_id']:{'trip_id':t['trip_id'],'stops':t['stops']} for t in facts['trips']}}
        if direction=='0':observations.update(trips=[],counts={'accepted':0,'polls':0},captured_from=None,captured_to=None,source='No matched outbound GPS sample; user arrivals remain unverified')
        ui_route={**route,'morning':morning,'segments':segments,'shape_start':0,'shape_end':route['shape_metres'],'study_date':reference['reference_date']}
        access={'candidate_priority_segments':masks[direction],'changes':{s['id']:[potential_lookup[e] for e in s['edges'] if e in potential_lookup] for s in segments},'segments':{s['id']:{'newly_unroutable':None,'status':'Individual interval not screened; combined prepared policy is screened'} for s in segments},'policy_masks':policy_masks,'applied_edges':screens['changes'],'screen':screens}
        directions[direction]={'route':ui_route,'cases':bycase,'access':access,'cameras':cameras,'camera_labels':labels,'observations':observations,'meta':{**raw['meta'],'direction':int(direction),'full_line':True,'replay_window':{'start':manifest['clips'][0]['start'],'end':manifest['clips'][0]['end']}}}
    roi=set(raw['replay_edge_ids']);common={'native_directions':directions,'geometry':[e for e in raw['geometry'] if e['id'] in roi],'replay_manifest':manifest,'replay_assets':'./line-701-full-assets/','study_midnight':reference['reference_date']+'T00:00:00+00:00','direction_cameras':{d:v['cameras'] for d,v in directions.items()},'full_traffic_summary':{'runs':len(raw['runs']),'trip_count':reference['trip_count'],'served_calls':reference['served_calls'],'begin':raw['meta']['begin'],'end':raw['meta']['end'],'native':True,'geometry_validation':json.loads((ROOT/'data/geometry-validation.json').read_text()),'demand_source':raw['meta']['traffic'],'vehicle_blocks':raw['meta']['vehicle_blocks']}}
    common['full_report']=report(raw)
    shutil.copy2(ROOT/'data/network-manifest.json',site/'701-full-network-manifest.json')
    shutil.copy2(ROOT/'data/route-geometry-audit.json',site/'701-full-geometry-audit.json')
    shutil.copy2(results_file,site/'701-full-experiments.json');shutil.copy2(ROOT/'data/routes.json',site/'701-full-routes.json')
    sources={'reference_date':reference['reference_date'],'native_study':'line-701-full','traffic':raw['meta']['traffic'],'vehicle_blocks':raw['meta']['vehicle_blocks'],
        'artifacts':{name:{'file':file,'sha256':digest(path)} for name,file,path in [('network','701-full-network-manifest.json',ROOT/'data/network-manifest.json'),('mapping','701-full-routes.json',ROOT/'data/routes.json'),('native_results','701-full-experiments.json',results_file),('replay','line-701-full-assets/manifest.json',manifest_file)]},
        'official_metadata':['701-official/metadata.json','701-extension/metadata.json','701-outbound/metadata.json'],'import_overlays':json.loads((ROOT/'data/route-import-overlays.json').read_text()),'geometry_control':common['full_traffic_summary']['geometry_validation']}
    (site/'701-full-sources.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2)+'\n')
    shutil.copytree(ROOT/'inspection-assets',site/'line-701-full-assets',dirs_exist_ok=True)
    return common

def report(raw):
    meta=raw['meta'];reference=raw['route_reference'];screen=raw['access'];timing={d:{s['stop_id'] for s in r['stops'] if s['designated_timing_point']} for d,r in reference['directions'].items()}
    control_timing=json.loads((ROOT/'data/geometry-validation.json').read_text())['timing_points']
    lines=['# 701: complete bidirectional native traffic simulation','','## What was actually run','',
      f"Native SUMO covers both complete directions, all {reference['trip_count']} scheduled workings and {reference['served_calls']} served scheduled calls: 63 towards Bolhão and 64 towards Codiceira/Ermesinde. Short workings retain their true endpoints; 960 unserved timetable cells are not invented departures.",
      f"The service reference is {reference['reference_date']}. Runs begin 05:00 and include service after midnight through 25:35, plus clearance until 27:35. Cases: {', '.join(meta['cases'])}; seeds: {meta['seeds']}; {len(raw['runs'])} native runs.",
      'The native buses share one regional road simulation with ordinary traffic, residents, taxis, bicycles and motorcycles. Both directions interact on the imported network. No other bus line or physical vehicle block/rotation is invented.',
      '', '## How to read the comparison','',
      'Baseline and priority use the same requested demand for each case/seed. Keep unfinished and unroutable requests in the comparison. A lower mean among completed trips cannot establish an improvement for everyone if other trips never finish. Entry waiting and in-network duration are reported separately; these are not door-to-door person travel times. These are conditional simulation outcomes, not measured recurring city delays.',
      '', '|Case|Policy|Seed|Inbound completed/63|Outbound completed/64|Served calls/6024|Unserved all vehicles|Late timing-point calls|Missing timing-point calls|', '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for run in raw['runs']:
      completed={d:sum(b['completed'] for b in run['buses'] if b['direction']==d) for d in ['1','0']};calls=[c for b in run['buses'] for c in b['stops']];timed=[c for b in run['buses'] for c in b['stops'] if c['stop_id'] in timing[b['direction']]]
      lines.append(f"|{run['case']}|{run['variant']}|{run['seed']}|{completed['1']}|{completed['0']}|{sum(c['arrival'] is not None for c in calls)}|{sum(g['unserved'] for g in run['groups'].values())}|{sum(c['lateness'] is not None and c['lateness']>0 for c in timed)}|{sum(c['arrival'] is None for c in timed)}|")
    lines+=['','## What changed in the prepared proposal','',f"Priority reserves one mapped bus-capable lane on {len(screen['changes'])} directed edges. General traffic is retained on {len(screen['general_traffic_retained'])} screened route edges. Existing bus-only lanes remain. The combined policy disconnects {screen['newly_unroutable']} of {screen['tested_pairs']} generated connector/OD test pairs.",
      'This is a generated connectivity screen, not proof of legal access, driveways, loading capacity, emergency routes or equitable access. Lane permissions change; the same imported geometry and signal assumptions are used in both policies.',
      '', '## What the animation shows','', 'The browser replay covers the complete line in both directions during 16:50–18:20, sampled from native output every 5 seconds and interpolated visually. The underlying traffic simulation uses its original one-second step. Vehicles are shown on route roads and roads meeting their junctions; the scene includes a wider 150m context. Numeric traffic totals cover the regional experiment. The replay is extracted from the same full-day execution as its numeric run. Scene/capture/network hashes and exact windows are validated through the replay manifest.',
      '', '## Evidence and limits','',meta['traffic'],meta['vehicle_blocks'],
      'One bus-only straight-turn exception near Asprela/Costa Cabral resolves a conflict between imported OSM restriction 16086845 and both the official outbound shape and OSM bus-route relation 10107392. It applies equally to baseline and priority; ordinary traffic keeps the imported restriction. This is a documented modelling assumption pending street/operator confirmation.',
      'Imported OSM one-way rules, lane counts and signals are not surveyed. Signals are guessed/unverified. Stops are snapped to native lanes with at least 15m usable stop space; the full bus-only validation must serve all 127 workings and 6024 calls. Ordinary traffic demand uses an explicit synthetic hourly profile, not metropolitan population, modal-choice calibration or observed OD counts. Dwell is fixed 20 seconds; the separate passenger/berth model retains its own assumptions. Real boarding loads, driver duties, other lines and fleet circulation remain missing.',
      'Timetable data is frozen for 28 October 2026. Direction 0 geometry and regional OSM have their own recorded retrieval dates; historical applicability is not established by the timetable date.',
      f"The bus-only control still has {control_timing['late_arrivals']} late timing-point arrivals out of {control_timing['planned_calls']} planned calls under the fixed-dwell and imported-signal assumptions. Traversable geometry does not establish a calibrated timetable model. Priority alone must not be presented as proving zero tardiness under these assumptions.",
      '', '## Reproduce and inspect','', '`./prototypes/line-701/full/run.sh --cases moderate,busy,late --seeds 17` (use `--seeds 17,42,73` for repeated seeds).',
      'Raw results: 701-full-experiments.json. Route mapping:701-full-routes.json. Street provenance:701-full-network-manifest.json. Replay provenance:line-701-full-assets/manifest.json. Timetable bundles:701-extension/ and 701-outbound/. [Source code and frozen input archive](https://github.com/Cabeda/invicta/tree/main/prototypes/line-701/full).',
      '', '## Transition interpretation','', 'This experiment first holds requested traffic demand constant to test street priority. Longer-term shifts from cars to reliable buses, cycling or walking are a separate scenario assumption, not an uptake prediction. The metropolitan transition calculator remains available in the earlier study. Deployment phases and costs still require an access survey, operator input, signal plans and local cost evidence.', '']
    return '\n'.join(lines)
