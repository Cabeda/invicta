"""Extend the frozen OSM network to Bolhão without changing the legacy study."""
from pathlib import Path
import datetime, gzip, hashlib, json, subprocess, urllib.request
import xml.etree.ElementTree as ET
import sumo

ROOT=Path(__file__).resolve().parent;DATA=ROOT/'data';LEGACY=ROOT.parent/'costa-cabral'
RAW=DATA/'raw';RAW.mkdir(exist_ok=True)
EXTRA_BOXES=[(-8.6143,41.1460,-8.6020,41.1560),(-8.6020,41.1460,-8.5897,41.1560)]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def prepare():
    manifest_file=DATA/'network-manifest.json';archive=DATA/'network.osm.xml.gz'
    if not archive.exists():
        original=LEGACY/'data/network.osm.xml.gz'
        inputs=[{'file':'../costa-cabral/data/network.osm.xml.gz','sha256':digest(original),'role':'Original frozen street-study source'}]
        sources=[ET.fromstring(gzip.decompress(original.read_bytes()))]
        for i,box in enumerate(EXTRA_BOXES):
            url='https://api.openstreetmap.org/api/0.6/map?bbox='+','.join(map(str,box))
            p=RAW/f'southern-tile-{i}.osm.xml'
            if not p.exists():
                with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Invicta-701-Prototype/0.2'}),timeout=90) as r:p.write_bytes(r.read())
            sources.append(ET.parse(p).getroot())
            inputs.append({'file':p.name,'url':url,'bbox':box,'sha256':digest(p),'bytes':p.stat().st_size})
        merged=ET.Element('osm',{'version':'0.6','generator':'Invicta frozen-source merge'})
        elements={}
        for source in sources:
            for e in source:
                if e.tag in ['node','way','relation']:elements[e.tag,e.get('id')]=e
        for kind in ['node','way','relation']:
            for (tag,ident),element in elements.items():
                if tag==kind:merged.append(element)
        with gzip.GzipFile(filename=str(archive),mode='wb',mtime=0) as f:f.write(ET.tostring(merged,encoding='utf-8',xml_declaration=True))
        manifest={'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':'OpenStreetMap API; original frozen area plus southern buffer to Bolhão',
                  'inputs':inputs,'merged_sha256':digest(archive),'licence':'ODbL, © OpenStreetMap contributors',
                  'baseline':'Unmodified OSM import of extended district, not a surveyed lane inventory. All policies use this same geometry.'}
        manifest_file.write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    manifest=json.loads(manifest_file.read_text())
    osm=RAW/'osm-tile-0.xml'
    if not osm.exists():osm.write_bytes(gzip.decompress(archive.read_bytes()))
    # Preserve the projection and coordinate offset so old observations stay comparable.
    location=ET.parse(LEGACY/'data/baseline.net.xml').getroot().find('location')
    offset=location.get('netOffset').split(',')
    command=[str(Path(sumo.SUMO_HOME)/'bin/netconvert'),'--osm-files',str(osm),'--output-file',str(DATA/'baseline.net.xml'),
             '--proj',location.get('projParameter'),'--offset.disable-normalization','true','--offset.x',offset[0],'--offset.y',offset[1],
             '--geometry.remove','--ramps.guess','--junctions.join','--tls.guess-signals','--tls.discard-simple','--tls.join',
             '--tls.default-type','actuated','--no-turnarounds','--output.street-names','true','--output.original-names','true',
             '--osm.bike-access','true','--keep-edges.by-vclass','passenger,bus,taxi,bicycle,motorcycle']
    result=subprocess.run(command,capture_output=True,text=True)
    (DATA/'network-import.log').write_text(result.stdout+'\n'+result.stderr)
    if result.returncode:raise RuntimeError(result.stderr[-1800:])
    manifest.update(network_sha256=digest(DATA/'baseline.net.xml'),projection=dict(location.attrib))
    manifest_file.write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    print('Extended Porto network imported:',DATA/'baseline.net.xml',flush=True)

if __name__=='__main__':prepare()
