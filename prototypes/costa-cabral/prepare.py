"""THROWAWAY prototype: freeze public inputs and import a real SUMO street network."""
from pathlib import Path
import urllib.request, urllib.parse, json, hashlib, datetime, gzip, subprocess, xml.etree.ElementTree as ET
import sumo, sumolib

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'; RAW=DATA/'raw'
RAW.mkdir(parents=True,exist_ok=True)
BBOX=(-8.6122,41.1558,-8.5750,41.1871) # western/southern/eastern/northern; buffered full named street
SOURCES={
 'bus_corridors.geojson':'https://dadosabertos.cm-porto.pt/dataset/54464c4e-9e19-11f1-84ed-6abdb6d5cf34/resource/5d3992d9-3437-4d59-84a6-ac5db23cf6a7/download/ext-corredores-bus-geojson.geojson',
 'loading.geojson':'https://dadosabertos.cm-porto.pt/dataset/5309382a-9e19-11f1-84ed-6abdb6d5cf34/resource/b8cdc156-9471-4a32-9349-cef306e46008/download/ext-cargas-e-descargas-geojson.geojson',
 'gtfs.zip':'https://dadosabertos.cm-porto.pt/dataset/71490e40-9e19-11f1-84ed-6abdb6d5cf34/resource/51340c18-0ef5-4895-b099-cf7247ea54f4/download/gtfs_feed.zip',
 'buses.json':'https://broker.fiware.urbanplatform.portodigital.pt/v2/entities?q=vehicleType%3D%3Dbus&limit=1000',
}
manifest={'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bbox':BBOX,'sources':[]}
def download(name,url,body=None):
 p=RAW/name
 if not p.exists() and (DATA/'frozen'/(name+'.gz')).exists():
  with gzip.open(DATA/'frozen'/(name+'.gz'),'rb') as f:p.write_bytes(f.read())
 if not p.exists():
  req=urllib.request.Request(url,data=body,headers={'User-Agent':'Invicta-Costa-Cabral-Prototype/0.1'})
  with urllib.request.urlopen(req,timeout=115) as r:p.write_bytes(r.read())
 data=p.read_bytes();manifest['sources'].append({'file':name,'url':url,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
 print(name,len(data),flush=True)
 return p
if not (RAW/'network.osm.xml').exists() and (DATA/'network.osm.xml.gz').exists():
 with gzip.open(DATA/'network.osm.xml.gz','rb') as f:(RAW/'network.osm.xml').write_bytes(f.read())
w,s,e,n=BBOX
query=f'[out:xml][timeout:100];(way["highway"]({s},{w},{n},{e});node["highway"="bus_stop"]({s},{w},{n},{e}););(._;>;);out body;'
osm=download('network.osm.xml','https://api.openstreetmap.org/api/0.6/map?bbox='+','.join(map(str,BBOX)))
if (DATA/'osm-source-urls.json').exists():manifest['sources'][-1]['tile_urls']=json.loads((DATA/'osm-source-urls.json').read_text())
for name,url in SOURCES.items():download(name,url)
# Freeze raw OSM for reruns; other large inputs are cached and identified by checksum.
with gzip.open(DATA/'network.osm.xml.gz','wb') as f:f.write(osm.read_bytes())
(DATA/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
cmd=[str(Path(sumo.SUMO_HOME)/'bin/netconvert'),'--osm-files',str(osm),'--output-file',str(DATA/'baseline.net.xml'),'--geometry.remove','--ramps.guess','--junctions.join','--tls.guess-signals','--tls.discard-simple','--tls.join','--tls.default-type','actuated','--no-turnarounds','--output.street-names','true','--output.original-names','true','--osm.bike-access','true','--keep-edges.by-vclass','passenger,bus,taxi,bicycle,motorcycle','--ptstop-output',str(DATA/'osm-stops.add.xml')]
print('Importing network…',flush=True)
r=subprocess.run(cmd,capture_output=True,text=True);(DATA/'network-import.log').write_text(r.stdout+'\n'+r.stderr)
print(r.stdout[-1800:]);print(r.stderr[-2500:]);r.check_returncode()

# The OSM importer expands some oneway=bus exceptions into a third lane.
# This pilot explicitly models two lanes total, one per mapped direction.
n=sumolib.net.readNet(str(DATA/'baseline.net.xml'));patch=ET.Element('edges');normalized=[]
for edge in n.getEdges():
 if edge.getName()=='Rua de Costa Cabral' and len(edge.getLanes())>1:
  normalized.append(edge.getID());ET.SubElement(patch,'edge',{'id':edge.getID(),'numLanes':'1'})
ET.ElementTree(patch).write(DATA/'two-lane-normalization.edg.xml',encoding='utf-8',xml_declaration=True)
r=subprocess.run([str(Path(sumo.SUMO_HOME)/'bin/netconvert'),'--sumo-net-file',str(DATA/'baseline.net.xml'),'--edge-files',str(DATA/'two-lane-normalization.edg.xml'),'--output-file',str(DATA/'normalized.net.xml'),'--no-turnarounds'],capture_output=True,text=True)
(DATA/'normalization.log').write_text(r.stdout+'\n'+r.stderr);r.check_returncode();(DATA/'normalized.net.xml').replace(DATA/'baseline.net.xml')
manifest['lane_normalization']={'premise':'Two lanes total, one in each mapped direction; survey required','directed_edges':normalized}
(DATA/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print('Two-lane normalization:',len(normalized),'directed stretches',flush=True)
