"""Match timestamped public GPS samples to route progress; never call ETAs arrivals."""
from pathlib import Path
import datetime, json, math
from zoneinfo import ZoneInfo
import sumolib
ROOT=Path(__file__).resolve().parent
def secs(text):
 h,m,s=map(int,text.split(':'));return h*3600+m*60+s
def analyse():
 route=json.loads((ROOT/'data/route.json').read_text());official=ROOT/'data/official'
 schedule=json.loads((official/'schedule.json').read_text())['schedule']
 def endpoint(trip):return next(s for s in trip['stops'] if s['stop_id']=='MPL4')['arrival_time']
 schedule=sorted(schedule,key=lambda t:secs(endpoint(t)))
 if len({endpoint(t) for t in schedule})!=len(schedule):raise RuntimeError('Ambiguous timetable anchor join')
 bystop={}
 for stop in route['stops']:
  raw=json.loads((official/f"{stop['stop_id']}_schedule.json").read_text())['schedule']
  calls=sorted([c for hour in raw.values() for c in hour],key=lambda c:secs(c['arrival_time']))
  if len(calls)!=len(schedule):raise RuntimeError('Incomplete per-stop timetable join')
  if len({c['arrival_time'] for c in calls})!=len(calls):raise RuntimeError('Ambiguous per-stop timetable rank join')
  bystop[stop['stop_id']]=calls
 full={}
 for i,trip in enumerate(schedule):
  if bystop['MPL4'][i]['arrival_time']!=endpoint(trip):raise RuntimeError('MPL4 anchor mismatch')
  full[trip['trip_id']]={'trip_id':trip['trip_id'],'stops':{sid:secs(calls[i]['arrival_time']) for sid,calls in bystop.items()}}
  times=list(full[trip['trip_id']]['stops'].values())
  if any(b<a for a,b in zip(times,times[1:])):raise RuntimeError('Non-monotonic trip/stop timetable association')
 net=sumolib.net.readNet(str(ROOT.parent/'costa-cabral/data/baseline.net.xml'),maxcache=0)
 timezone=ZoneInfo('Europe/Lisbon');day=datetime.date.fromisoformat(route['study_date'])
 points=route['full_shape'];lengths=route['shape_lengths'];traces={};counts={'polls':0,'raw_rows':0,'duplicates':0,'unmatched_trip':0,'wrong_service_date':0,'stale_or_future':0,'off_route':0,'accepted':0};seen=set()
 file=ROOT/'data/observations/positions.ndjson'
 records=[json.loads(l) for l in file.read_text().splitlines()] if file.exists() else []
 for record in records:
  if 'vehicles' not in record:continue
  counts['polls']+=1;received=datetime.datetime.fromisoformat(record['received_at'])
  for v in record['vehicles']:
   counts['raw_rows']+=1
   if not v.get('observed_at') or not v.get('coordinates'):continue
   when=datetime.datetime.fromisoformat(v['observed_at'].replace('Z','+00:00'));age=(received-when).total_seconds()
   key=(v.get('trip_id'),v['observed_at'],tuple(v['coordinates']))
   if key in seen:counts['duplicates']+=1;continue
   seen.add(key)
   if v.get('trip_id') not in full:counts['unmatched_trip']+=1;continue
   if when.astimezone(timezone).date()!=day:counts['wrong_service_date']+=1;continue
   if not -10<=age<=90:counts['stale_or_future']+=1;continue
   x,y=net.convertLonLat2XY(*v['coordinates']);best=None
   previous=traces.get(v['trip_id'],[]);floor=previous[-1]['progress']-35 if previous else -math.inf
   for i,(a,b) in enumerate(zip(points,points[1:])):
    dx,dy=b[0]-a[0],b[1]-a[1];den=dx*dx+dy*dy
    f=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/den)) if den else 0
    progress=lengths[i]+f*math.sqrt(den)
    if progress<floor:continue
    distance=math.hypot(x-a[0]-f*dx,y-a[1]-f*dy)
    if best is None or distance<best[0]:best=(distance,progress)
   if best is None or best[0]>40:counts['off_route']+=1;continue
   sample={'observed_at':when.isoformat(),'received_at':record['received_at'],'progress':best[1],'cross_track_metres':round(best[0],1),
           'point':[x,y],'vehicle_id':v.get('vehicle_id')}
   traces.setdefault(v['trip_id'],[]).append(sample);counts['accepted']+=1
 midnight=datetime.datetime.combine(day,datetime.time(),tzinfo=timezone)
 summaries=[]
 for trip,rows in traces.items():
  rows.sort(key=lambda r:r['observed_at']);passages=[]
  for stop in route['stops']:
   for a,b in zip(rows,rows[1:]):
    dt=(datetime.datetime.fromisoformat(b['observed_at'])-datetime.datetime.fromisoformat(a['observed_at'])).total_seconds()
    if 0<dt<=90 and a['progress']<=stop['shape_progress']<=b['progress'] and b['progress']>=a['progress']:
     sa=(datetime.datetime.fromisoformat(a['observed_at'])-midnight).total_seconds();sb=(datetime.datetime.fromisoformat(b['observed_at'])-midnight).total_seconds();scheduled=full[trip]['stops'][stop['stop_id']]
     passages.append({'stop_id':stop['stop_id'],'from':a['observed_at'],'to':b['observed_at'],
                      'scheduled_seconds':scheduled,'lateness_low':sa-scheduled,'lateness_high':sb-scheduled,
                      'kind':'GPS-derived passage window; not observed door-open arrival'})
     break
  relevant=[r for r in rows if route['shape_start']-100<=r['progress']<=route['shape_end']+100]
  summaries.append({'trip_id':trip,'samples':len(rows),'section_samples':len(relevant),'first':rows[0]['observed_at'],'last':rows[-1]['observed_at'],
                    'passages':passages,'points':relevant,'scheduled':full[trip]['stops']})
 accepted_received=[r['received_at'] for rows in traces.values() for r in rows]
 output={'counts':counts,'trips':summaries,'timetables':full,'captured_from':min(accepted_received) if accepted_received else None,
         'captured_to':max(accepted_received) if accepted_received else None,
         'source':'Public Porto Digital Vehicle broker; received timestamps and reported observation timestamps retained',
         'quality':'Exact current trip_id join and Lisbon study-date match; observation age -10..90s; cross-track distance <=40m; crossing bracket <=90s. GPS passage is not a boarding/arrival event.',
         'scope':'Short evening sample on 28 October 2026, not historical morning calibration; partial coverage stays missing.'}
 (ROOT/'data/observations-summary.json').write_text(json.dumps(output,ensure_ascii=False,indent=2))
 print('Observation quality:',counts,'passage windows',sum(len(t['passages']) for t in summaries),flush=True)
 return output
if __name__=='__main__':analyse()
