"""Bounded, read-only sampling of public timestamped 701 inbound bus positions."""
from pathlib import Path
import argparse, datetime, json, time, urllib.request
ROOT = Path(__file__).resolve().parent
URL = 'https://broker.fiware.urbanplatform.portodigital.pt/v2/entities?q=vehicleType%3D%3Dbus&limit=1000'

def collect(duration, interval, output):
    deadline = time.monotonic() + duration
    count = 0
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('a') as f:
        while time.monotonic() < deadline:
            now = datetime.datetime.now(datetime.timezone.utc)
            try:
                request = urllib.request.Request(URL, headers={'User-Agent': 'Invicta-701-Prototype/0.1'})
                with urllib.request.urlopen(request, timeout=20) as response: data = json.load(response)
                rows = []
                for entity in data:
                    annotations = entity.get('annotations', {}).get('value', [])
                    if 'stcp:route:701' not in annotations or 'stcp:sentido:1' not in annotations: continue
                    trip = next((a.split('stcp:nr_viagem:', 1)[1] for a in annotations if a.startswith('stcp:nr_viagem:')), None)
                    rows.append({'entity_id': entity['id'], 'vehicle_id': entity.get('fleetVehicleId', {}).get('value'),
                                 'trip_id': trip, 'observed_at': entity.get('observationDateTime', {}).get('value'),
                                 'coordinates': entity.get('location', {}).get('value', {}).get('coordinates'),
                                 'speed': entity.get('speed', {}).get('value')})
                f.write(json.dumps({'received_at': now.isoformat(), 'source': URL, 'route': '701', 'direction': 1, 'vehicles': rows}, ensure_ascii=False) + '\n')
                f.flush(); count += 1
                print(now.isoformat(), len(rows), 'inbound observations; poll', count, flush=True)
            except Exception as error:
                f.write(json.dumps({'received_at': now.isoformat(), 'error': str(error)}) + '\n'); f.flush()
                print('Poll unavailable:', type(error).__name__, flush=True)
            remaining = deadline - time.monotonic()
            if remaining > 0: time.sleep(min(interval, remaining))
    return count

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--duration', type=int, default=900)
    parser.add_argument('--interval', type=int, default=15)
    parser.add_argument('--output', type=Path, default=ROOT/'data/observations/positions.ndjson')
    args = parser.parse_args()
    collect(args.duration, args.interval, args.output)
