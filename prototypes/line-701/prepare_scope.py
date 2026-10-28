"""Compile the verified Porto extent into the existing frozen source-facts schema."""
from pathlib import Path
import json, shutil
ROOT=Path(__file__).resolve().parent;DATA=ROOT/'data'
def prepare():
    extension=json.loads((DATA/'official-extension/extension-facts.json').read_text())
    facts=json.loads((DATA/'source-facts.json').read_text());b=extension['boundary'];entry=b['municipal_entry']
    facts['segment']=extension['segment'];facts['schedule'].update(extension['schedule'])
    facts['municipality']={**b,'entry_lonlat':[entry['lon'],entry['lat']],
                           'approach_metres':b['municipal_entry_to_ars3_shape_length_m_epsg3763'],
                           'shape_metres':b['municipal_entry_to_final_shape_length_m_epsg3763']}
    facts['extension_source_bundle']='data/official-extension'
    facts['source_urls'].update(extension['source_urls'])
    facts['limitations']=['Frozen 28 October 2026 reference, not live service.',
       'MPL4 and 0BLRB are designated timing points; other Porto calls are intermediate published references.',
       'Per-stop trip IDs are derived by unique matching against route timing-point anchors; source endpoint omits IDs.',
       'No official timetable is supplied at the municipal boundary; native entry lead is assumed.',
       'Full-line passenger/service propagation is an assumed operational model, distinct from the Porto SUMO street simulation.']
    (DATA/'source-facts.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2))
    for stop in extension['segment']['stops']:
        source=DATA/'official-extension'/f"stop_schedule_{stop['stop_id']}.json"
        # Preserve original raw responses when unchanged; append the three new stop inputs.
        target=DATA/'official'/f"{stop['stop_id']}_schedule.json"
        if not target.exists():shutil.copy2(source,target)
    print('Scope:',len(facts['segment']['stops']),'Porto stops through',facts['segment']['end_stop_id'],flush=True)
if __name__=='__main__':prepare()
