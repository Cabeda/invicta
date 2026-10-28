"""Proposal outputs from frozen SUMO trajectories: captioned MP4s and a static website."""
from pathlib import Path
import argparse, json, math, statistics, subprocess, shutil, gzip, hashlib, zipfile
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent; SITE=ROOT/'proposal'; SITE.mkdir(exist_ok=True)
W,H,FPS,DURATION=1920,1080,25,60
INK='#153b31'; MUTED='#5b7166'; GREEN='#177455'; PAPER='#f4f5ee'; LINE='#d4dfd6'; AMBER='#986320'
COLORS={'bus':'#177455','resident':'#466fba','taxi':'#bb873c','bicycle':'#2e9697','motorcycle':'#87699b','through':'#969b96','background':'#969b96','crossing':'#4a648c'}
TEXT={
'pt':{'eyebrow':'INVICTA / PROPOSTA PARA DISCUSSÃO','title':'Rua de Costa Cabral.','headline':'Autocarros a horas.','sub':'Cumprir horários e servir moradores, clientes e comércio local.','badge':'CONCEITO · TRÁFEGO SIMULADO · POR CALIBRAR','baseline':'Modelo de referência','restricted':'Acesso condicionado','modes':['Autocarros','Moradores','Táxis','Bicicletas','Motociclos'],'cross':'Cruzamentos diretos mantidos','crosssub':'Automóveis podem atravessar, sem circular ao longo da rua.','scheme':'Esquema de acesso; não é um projeto de execução.','before':'REFERÊNCIA','after':'PROPOSTA','replay':'Os mesmos minutos. Duas regras de acesso.','clip':'Replay SUMO · semente 17 · veículos com tamanho ampliado','bus':'Autocarros','resident':'Acesso local','others':'Outros veículos','metrics':'Horários e acesso a validar.','ontime':'Chegadas à última paragem até 3 min tarde*','busmean':'Média no corredor, viagens concluídas','busmetric':'Tempo médio dos autocarros no corredor','route':'pedidos sem percurso permitido na proposta*','routefoot':'*Limiar ilustrativo de 3 min; não avalia partidas adiantadas. Rede modelada limitada.','next':'Medir → validar → testar no terreno','end':'Validar horários e acesso à vida local.','foot':'Procura assumida · horário STCP de 2 set. 2026 · sem previsão validada','mean':'Hipótese moderada · médias de 3 sementes','phase':'Dados e elegibilidade dos moradores; desenho de um ensaio reversível.'},
'en':{'eyebrow':'INVICTA / PROPOSAL FOR DISCUSSION','title':'Rua de Costa Cabral.','headline':'On-time buses.','sub':'Meeting schedules while serving residents, shoppers and local businesses.','badge':'CONCEPT · SIMULATED TRAFFIC · UNCALIBRATED','baseline':'Baseline model','restricted':'Restricted access','modes':['Buses','Residents','Taxis','Bikes','Motorcycles'],'cross':'Direct junction crossings stay open','crosssub':'Ordinary cars may cross, without driving along the street.','scheme':'Access diagram; not an engineering design.','before':'BASELINE','after':'PROPOSAL','replay':'The same minutes. Two access rules.','clip':'SUMO replay · seed 17 · vehicle symbols enlarged','bus':'Buses','resident':'Local access','others':'Other vehicles','metrics':'Timetables and access to validate.','ontime':'Final-stop arrivals no more than 3 min late*','busmean':'Corridor mean, completed trips','busmetric':'Mean bus journey time within the corridor','route':'requests without a permitted route in the proposal*','routefoot':'*Illustrative 3-minute threshold; early departures not assessed. Limited model area.','next':'Measure → validate → trial','end':'Validate timetables and everyday local access.','foot':'Assumed demand · STCP schedule dated 2 Sep 2026 · not a validated forecast','mean':'Moderate demand assumption · means across 3 seeds','phase':'Data and resident eligibility; design a reversible field trial.'}}

@lru_cache(None)
def font(size,bold=False):
 choices=[Path('/System/Library/Fonts/Supplemental')/('Arial Bold.ttf' if bold else 'Arial.ttf'),Path('/usr/share/fonts/truetype/dejavu')/('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')]
 return ImageFont.truetype(str(next(p for p in choices if p.exists())),size)

def write(draw,xy,s,size=28,fill=INK,bold=False,anchor=None):draw.text(xy,s,font=font(size,bold),fill=fill,anchor=anchor)
def wrap(draw,s,width,size=28,bold=False):
 lines=[];line=''
 for word in s.split():
  trial=(line+' '+word).strip()
  if draw.textlength(trial,font=font(size,bold))>width and line:lines.append(line);line=word
  else:line=trial
 if line:lines.append(line)
 return lines

def point_at(shape,pos):
 for a,b in zip(shape,shape[1:]):
  length=math.dist(a,b)
  if pos<=length:
   f=pos/length if length else 0;return [a[0]+f*(b[0]-a[0]),a[1]+f*(b[1]-a[1])]
  pos-=length
 return shape[-1]

def build_data():
 result=json.loads((ROOT/'results.json').read_text());replays=json.loads((ROOT/'media/replays.json').read_text());geometry=result['geometry'];edges={e['id']:e for e in geometry};labels=[];seen=set()
 wanted=['COMBATENTES','PIRES DE LIMA','CONDE FERREIRA','S.TA JUSTA','AREOSA']
 for bus in result['buses']:
  for st in bus['stops']:
   if st['name'] in wanted and st['name'] not in seen:
    seen.add(st['name']);labels.append({'name':st['name'],'point':point_at(edges[st['edge']]['shape'],st['pos'])})
 pts=[p for e in geometry if e['corridor'] for p in e['shape']];box=[min(p[0] for p in pts)-300,min(p[1] for p in pts)-250,max(p[0] for p in pts)+300,max(p[1] for p in pts)+250]
 cameras={'corridor':box}
 for key,name in [('combatentes','COMBATENTES'),('conde','CONDE FERREIRA'),('areosa','AREOSA')]:
  label=next(x for x in labels if x['name']==name);x,y=label['point'];cameras[key]=[x-360,y-320,x+360,y+320]
 stats={}
 for case in result['meta']['cases']:
  stats[case]={}
  for policy in ['baseline','restricted']:
   runs=[r for r in result['runs'] if r['case']==case and r['policy']==policy]
   stats[case][policy]={'bus_minutes':statistics.mean(r['groups']['bus']['mean_duration'] for r in runs)/60,'bus_on_time':statistics.mean(r['groups']['bus']['on_time_pct'] for r in runs),'unserved':statistics.mean(sum(g['unserved'] for g in r['groups'].values()) for r in runs),'no_route':statistics.mean(r['unroutable'] for r in runs),'resident_minutes':statistics.mean(r['groups']['resident']['mean_duration'] for r in runs)/60,'crossing_completed':statistics.mean(r['groups']['crossing']['completed'] for r in runs)}
 # Keep provenance hashes; omit local execution paths from the public presentation.
 clean={k:{key:value for key,value in r.items() if key not in ['command']} for k,r in replays.items()}
 return {'geometry':geometry,'cameras':cameras,'labels':labels,'replays':clean,'stats':stats,'assumptions':result['meta'],'sources':result['manifest'],'colors':COLORS,'clip':{'start':720,'end':1440,'step':4,'seed':17}}

def project(p,box,size):
 width,height=size;x0,y0,x1,y1=box;scale=min((width-48)/(x1-x0),(height-48)/(y1-y0));ox=(width-(x1-x0)*scale)/2;oy=(height-(y1-y0)*scale)/2
 return (ox+(p[0]-x0)*scale, height-oy-(p[1]-y0)*scale)

def map_image(data,policy,camera='corridor',size=(870,590)):
 im=Image.new('RGB',size,'#f7f9f4');d=ImageDraw.Draw(im);box=data['cameras'][camera]
 for e in data['geometry']:
  if not any(box[0]-100<=p[0]<=box[2]+100 and box[1]-100<=p[1]<=box[3]+100 for p in e['shape']):continue
  points=[project(p,box,size) for p in e['shape']]
  if len(points)>1:d.line(points,fill='#d4ded5',width=2)
 for e in data['geometry']:
  if e['corridor']:
   points=[project(p,box,size) for p in e['shape']]
   if len(points)>1:d.line(points,fill=GREEN if policy=='restricted' else '#8a978b',width=7)
 for label in data['labels']:
  p=project(label['point'],box,size)
  if 30<p[0]<size[0]-30 and 20<p[1]<size[1]-20:
   d.ellipse((p[0]-4,p[1]-4,p[0]+4,p[1]+4),fill='white',outline=GREEN,width=2)
   name=label['name'].title();tx=min(p[0]+12,size[0]-160)
   d.text((tx,p[1]-22),name,font=font(16,True),fill=INK,stroke_width=3,stroke_fill='#f7f9f4')
 write(d,(size[0]-35,20),'N',14,bold=True);d.line((size[0]-29,55,size[0]-29,40),fill=INK,width=2)
 return im

def positions(replay,t):
 i=max(0,min(len(replay['frames'])-1,int((t-replay['start'])/replay['step'])));a=replay['frames'][i];b=replay['frames'][min(i+1,len(replay['frames'])-1)];f=max(0,min(1,(t-a['t'])/replay['step']));nxt={v[0]:v for v in b['vehicles']};out=[]
 for row in a['vehicles']:
  v=nxt.get(row[0],row);angle=row[3]+((v[3]-row[3]+180)%360-180)*f
  out.append((row[0],row[1]+(v[1]-row[1])*f,row[2]+(v[2]-row[2])*f,angle,row[4]))
 return out

def traffic(im,data,replay,t,camera):
 d=ImageDraw.Draw(im);box=data['cameras'][camera];size=im.size
 # Buses on top; symbols are deliberately legible rather than physically scaled.
 rows=positions(replay,t);rows.sort(key=lambda v:replay['vehicles'][v[0]]['group']=='bus')
 for ident,x,y,angle,speed in rows:
  px,py=project((x,y),box,size)
  if not 4<px<size[0]-4 or not 4<py<size[1]-4:continue
  group=replay['vehicles'][ident]['group'];color=COLORS.get(group,'#969b96');r=math.radians(angle);length,width=(13,5) if group=='bus' else ((5,3) if group=='bicycle' else (7,3.5));dx,dy=math.sin(r),-math.cos(r);sx,sy=-dy,dx
  poly=[(px+dx*a+sx*b,py+dy*a+sy*b) for a,b in [(-length/2,-width/2),(length/2,-width/2),(length/2,width/2),(-length/2,width/2)]]
  if group=='bus':d.line(poly+[poly[0]],fill='white',width=3)
  d.polygon(poly,fill=color)
 return im

def clock(t):return f'{8+int(t)//3600:02}:{int(t)%3600//60:02}:{int(t)%60:02}'
def num(n,lang):return f'{n:.1f}'.replace('.',',') if lang=='pt' else f'{n:.1f}'
def footer(d,tx):
 d.rectangle((0,1015,W,H),fill='#e5ecdf');write(d,(62,1034),tx['foot'],22,fill=MUTED);write(d,(W-62,1034),'OSM © contributors / ODbL',19,fill=MUTED,anchor='ra')
def pill(d,box,text,fill=GREEN,textfill='white',size=20):d.rounded_rectangle(box,radius=13,fill=fill);write(d,(box[0]+14,box[1]+9),text,size,fill=textfill,bold=True)

def frame(data,lang,second,case='moderate',camera='corridor'):
 tx=TEXT[lang];im=Image.new('RGB',(W,H),PAPER);d=ImageDraw.Draw(im)
 write(d,(62,36),tx['eyebrow'],21,fill=GREEN,bold=True);pill(d,(1030,28,1858,78),tx['badge'],fill='#e4eadb',textfill=GREEN,size=20)
 if second<7:
  bg=map_image(data,'restricted',size=(790,840));im.paste(bg,(1068,122));d=ImageDraw.Draw(im)
  write(d,(62,168),tx['title'],89,bold=True);write(d,(62,288),tx['headline'],61,bold=True)
  for i,line in enumerate(wrap(d,tx['sub'],910,35)):write(d,(65,390+i*48),line,35,fill=MUTED)
  write(d,(65,570),'Marquês → Areosa',36,bold=True)
  for i,label in enumerate(tx['modes']):pill(d,(65+(i%3)*300,680+(i//3)*70,345+(i%3)*300,735+(i//3)*70),label,fill='#e4eadb',textfill=GREEN,size=23)
  write(d,(65,880),tx['cross'],32,bold=True)
 elif second<15:
  write(d,(62,122),tx['headline'],68,bold=True);write(d,(65,220),tx['cross'],34,fill=MUTED)
  # Two corridor directions, with a direct perpendicular crossing. Schematic only.
  d.rounded_rectangle((60,330,1860,700),radius=25,fill='#dce9dc');d.line((60,515,1860,515),fill='white',width=5)
  for x in [270,690,1110,1530]:
   d.line((x-65,430,x+70,430),fill=GREEN,width=12);d.polygon([(x+70,430),(x+40,409),(x+40,451)],fill=GREEN)
   d.line((x-65,600,x+70,600),fill=GREEN,width=12);d.polygon([(x-65,600),(x-35,579),(x-35,621)],fill=GREEN)
  d.rectangle((905,310,1015,720),fill='#aeb9ad');d.line((960,300,960,730),fill='white',width=4)
  for y in [365,650]:d.rounded_rectangle((932,y-28,955,y+28),radius=5,fill='#64746d')
  for i,label in enumerate(tx['modes']):pill(d,(65+i*360,770,395+i*360,830),label,fill='#e4eadb',textfill=GREEN,size=25)
  write(d,(65,880),tx['crosssub'],30,bold=True);write(d,(65,940),tx['scheme'],22,fill=MUTED)
 elif second<51:
  write(d,(62,102),tx['replay'],51,bold=True);write(d,(65,177),tx['clip'],24,fill=MUTED)
  t=720+(second-15)*20
  for policy,x in [('baseline',62),('restricted',992)]:
   pill(d,(x,233,x+868,283),tx[policy],fill=GREEN if policy=='restricted' else '#7b887b',size=25)
   panel=MAPS[policy].copy();traffic(panel,data,data['replays'][case+'-'+policy],t,camera);im.paste(panel,(x,300));d=ImageDraw.Draw(im)
  pill(d,(790,905,1130,970),clock(t),fill=INK,size=37)
  for i,(label,color) in enumerate([(tx['bus'],GREEN),(tx['resident'],COLORS['resident']),(tx['others'],'#969b96')]):
   px=62+i*240;d.rounded_rectangle((px,929,px+32,943),radius=3,fill=color);write(d,(px+45,919),label,24,fill=MUTED)
 else:
  write(d,(62,125),tx['metrics'],62,bold=True)
  case_caption={'pt':{'moderate':'Procura moderada','busy':'Mais tráfego de atravessamento','residents':'Mais acesso local'},'en':{'moderate':'Moderate demand','busy':'More through traffic','residents':'More local access'}}[lang][case]
  mean_caption=case_caption+(' · médias de 3 sementes · por calibrar' if lang=='pt' else ' · mean of 3 seeds · uncalibrated')
  write(d,(65,215),mean_caption,29,fill=MUTED)
  a=data['stats'][case]['baseline'];b=data['stats'][case]['restricted']
  d.rounded_rectangle((62,320,1160,710),radius=25,fill='white',outline=LINE,width=2)
  write(d,(105,355),tx['ontime'],31,bold=True)
  write(d,(105,430),num(a['bus_on_time'],lang)+'%',82,fill='#7b887b',bold=True);write(d,(575,446),'→',76,fill=MUTED);write(d,(730,430),num(b['bus_on_time'],lang)+'%',82,fill=GREEN,bold=True)
  write(d,(105,568),tx['baseline'],26,fill=MUTED);write(d,(735,568),tx['restricted'],26,fill=GREEN)
  write(d,(105,638),tx['busmean']+': '+num(a['bus_minutes'],lang)+' → '+num(b['bus_minutes'],lang)+' min',23,fill=MUTED)
  d.rounded_rectangle((1205,320,1858,710),radius=25,fill='#eee4cd')
  write(d,(1245,355),str(round(b['no_route'])),100,fill=AMBER,bold=True)
  for i,line in enumerate(wrap(d,tx['route'],540,31,True)):write(d,(1245,490+i*44),line,31,fill=AMBER,bold=True)
  write(d,(65,748),tx['routefoot'],24,fill=MUTED);write(d,(65,825),tx['next'],43,bold=True);write(d,(65,902),tx['end'],31,fill=GREEN)
 footer(ImageDraw.Draw(im),tx)
 return im

MAPS={}
def render_video(data,lang,case,camera,fps=FPS):
 global MAPS
 MAPS={p:map_image(data,p,camera,size=(868,590)) for p in ['baseline','restricted']}
 target=SITE/f'costa-cabral-{lang}.mp4';log=ROOT/'media'/f'encode-{lang}.log'
 cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(fps),'-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(target)]
 with log.open('w') as err:
  p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=err)
  for i in range(DURATION*fps):
   p.stdin.write(frame(data,lang,i/fps,case,camera).tobytes())
   if i%(fps*15)==0:print(lang,'video',i//fps,'/',DURATION,'seconds',flush=True)
  p.stdin.close();code=p.wait()
  if code:raise RuntimeError(log.read_text())
 for sec,label in [(3,'intro'),(11,'access'),(33,'comparison'),(55,'outcomes')]:frame(data,lang,sec,case,camera).save(ROOT/'media'/f'{lang}-{label}.jpg',quality=90)
 frame(data,lang,3,case,camera).save(SITE/f'poster-{lang}.jpg',quality=90)
 info_file=SITE/'video-info.json';info=json.loads(info_file.read_text()) if info_file.exists() else {}
 info[lang]={'file':target.name,'case':case,'camera':camera,'duration_seconds':DURATION,'fps':fps,'width':W,'height':H,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
 info_file.write_text(json.dumps(info,indent=2))
 print('Video saved:',target,flush=True)

def export_site(data):
 if (SITE/'video-info.json').exists():data['video_info']=json.loads((SITE/'video-info.json').read_text())
 compact=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
 page=(ROOT/'proposal.template.html').read_text().replace('__PRESENTATION_DATA__',compact)
 (SITE/'index.html').write_text(page)
 lab=(ROOT/'costa-cabral.prototype.html').read_text().replace('href="proposal/index.html"','href="index.html"')
 lab=lab.replace('<a class="presentation-link" href="costa-cabral-proposal-site.zip" download>Export website (.zip)</a>','')
 (SITE/'experiment.html').write_text(lab)
 shutil.copy2(ROOT/'results.csv',SITE/'results.csv');shutil.copy2(ROOT/'FINDINGS.md',SITE/'findings.md')
 (SITE/'sources.json').write_text(json.dumps(data['sources'],ensure_ascii=False,indent=2))
 readme='''COSTA CABRAL — STATIC PROPOSAL WEBSITE\n\nOpen index.html directly, or serve this folder with: python3 -m http.server 8080\n\nPublish by uploading ALL extracted files together to any static website host.\nNo backend, database, API key or build step is required.\nKeep filenames and relative paths intact. index.html is the entry point.\n\nPT/EN language switch. Synchronized actual SUMO trajectory replays.\nThree precomputed demand cases; these controls do not run new simulations.\nMP4 videos have burned-in PT or EN captions.\nThe browser can record the selected view to WebM if MediaRecorder is supported.\n\nThese are simulated trajectories and uncalibrated outcomes, not observed traffic\nor a validated forecast. Input schedule: 2 Sep 2026. Seed 17 in replays;\nreported metrics aggregate seeds 17,42,73. Unserved demand remains explicit.\nVehicle symbols are enlarged and motion interpolates four-second samples.\n\nOSM (c) OpenStreetMap contributors, ODbL. Municipal GIS/STCP catalogue: CC0.\nSource URLs/hashes in sources.json. Detailed model limitations in findings.md.\n'''
 (SITE/'README.txt').write_text(readme)
 archive=ROOT/'costa-cabral-proposal-site.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for path in sorted(SITE.iterdir()):
   if path.is_file():z.write(path,path.name)
 print('Website bundle:',archive,flush=True)

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--skip-video',action='store_true');ap.add_argument('--language',choices=['pt','en','both'],default='both');ap.add_argument('--case',choices=['moderate','busy','residents'],default='moderate');ap.add_argument('--camera',choices=['corridor','combatentes','conde','areosa'],default='corridor');args=ap.parse_args();data=build_data()
 with gzip.GzipFile(filename=str(ROOT/'media/replays.json.gz'),mode='wb',mtime=0) as f:f.write((ROOT/'media/replays.json').read_bytes())
 if not args.skip_video:
  for lang in (['pt','en'] if args.language=='both' else [args.language]):render_video(data,lang,args.case,args.camera)
 export_site(data)
