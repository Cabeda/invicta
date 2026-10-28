"""Capture actual SUMO trajectories for presentation. Reuses frozen seed-17 inputs."""
from pathlib import Path
import argparse, subprocess, xml.etree.ElementTree as ET, json, hashlib, datetime
from concurrent.futures import ThreadPoolExecutor
import sumo
ROOT=Path(__file__).resolve().parent
START,STOP,STEP=720,1440,4

def capture(case,policy,refresh=False):
 source=ROOT/'runs'/f'{case}-{policy}-17';target=ROOT/'runs/media'/f'{case}-{policy}-17';target.mkdir(parents=True,exist_ok=True)
 output=ROOT/'media'/f'{case}-{policy}.json'
 inputs=[ROOT/'data'/f'{policy}.net.xml',source/'routes.rou.xml',source/'additional.add.xml']
 hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
 if output.exists() and not refresh:
  old=json.loads(output.read_text())
  if old['input_hashes']==hashes:return old
 fcd=target/'trajectory.xml'
 cmd=[str(Path(sumo.SUMO_HOME)/'bin/sumo'),'--net-file',str(inputs[0]),'--route-files',str(inputs[1]),'--additional-files',str(inputs[2]),'--begin','0','--end',str(STOP+STEP),'--seed','17','--time-to-teleport','-1','--no-step-log','true','--duration-log.disable','true','--xml-validation','never','--fcd-output',str(fcd),'--device.fcd.begin',str(START),'--device.fcd.period',str(STEP),'--fcd-output.attributes','id,x,y,angle,speed,type']
 # Remove statistics definitions from the replay's additional file so the frozen run outputs are untouched.
 add=ET.parse(inputs[2]);ar=add.getroot()
 for el in list(ar):
  if el.tag=='edgeData':ar.remove(el)
 additional=target/'stops.add.xml';add.write(additional,encoding='utf-8',xml_declaration=True)
 cmd[cmd.index('--additional-files')+1]=str(additional)
 p=subprocess.run(cmd,capture_output=True,text=True);(target/'capture.log').write_text(p.stdout+'\n'+p.stderr)
 if p.returncode:raise RuntimeError(p.stderr[-2000:])
 vehicles=[];ids={};frames=[]
 for _,el in ET.iterparse(fcd,events=['end']):
  if el.tag!='timestep':continue
  t=float(el.get('time'))
  if START<=t<=STOP:
   rows=[]
   for v in el:
    vid=v.get('id')
    if vid not in ids:ids[vid]=len(vehicles);vehicles.append({'id':vid,'group':v.get('type',vid.split('_')[0])})
    rows.append([ids[vid],round(float(v.get('x')),1),round(float(v.get('y')),1),round(float(v.get('angle'))),round(float(v.get('speed')),1)])
   frames.append({'t':t,'vehicles':rows})
  el.clear()
 data={'case':case,'policy':policy,'seed':17,'start':START,'end':STOP,'step':STEP,'frames':frames,'vehicles':vehicles,'input_hashes':hashes,'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':'SUMO 1.28.0 FCD; simulated trajectories, not observed GPS','command':cmd}
 output.write_text(json.dumps(data,separators=(',',':')))
 print(case,policy,len(frames),'frames',len(vehicles),'vehicles',flush=True)
 return data

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--refresh',action='store_true');args=ap.parse_args()
 tasks=[(c,p) for c in ['moderate','busy','residents'] for p in ['baseline','restricted']]
 with ThreadPoolExecutor(max_workers=3) as ex:replays=list(ex.map(lambda x:capture(*x,refresh=args.refresh),tasks))
 (ROOT/'media/replays.json').write_text(json.dumps({x['case']+'-'+x['policy']:x for x in replays},separators=(',',':')))
 print('Saved six replay datasets',flush=True)
