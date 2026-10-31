"""Nested synthetic traffic levels; preserve each selected physical request."""
import hashlib
import json
import math


def select_traffic(requests, fraction=1):
    if isinstance(fraction, bool) or not isinstance(fraction, (int, float)) or not math.isfinite(fraction) or not 0 <= fraction <= 1:
        raise ValueError('Traffic fraction must be a finite number between 0 and 1')
    if len({row['id'] for row in requests}) != len(requests):
        raise ValueError('Traffic catalogue contains duplicate request identities')
    threshold = int(fraction * 2 ** 256)
    selected = [row for row in requests if int.from_bytes(hashlib.sha256(
        ('invicta.traffic-ramp.v1:' + row['id']).encode()).digest(), 'big') < threshold]
    signature = lambda rows: hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    return selected, {'schema': 'invicta.traffic-ramp.v1', 'fraction': fraction,
        'catalogue_requests': len(requests), 'selected_requests': len(selected),
        'catalogue_sha256': signature(requests), 'selected_sha256': signature(selected),
        'meaning': 'Nested synthetic workload, not measured traffic or a mode-shift forecast.'}
