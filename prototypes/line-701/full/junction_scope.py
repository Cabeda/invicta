"""Audit a native junction rebuild against an explicit, reviewed footprint."""
import xml.etree.ElementTree as ET


def audit_scope(before, after, *, nodes, controllers, removed_roads=()):
    original, candidate = ET.parse(before).getroot(), ET.parse(after).getroot()
    roads = {e.get('id'): e for e in original.findall('edge') if not e.get('function')}
    new_roads = {e.get('id'): e for e in candidate.findall('edge') if not e.get('function')}

    def internal(ident):
        return any(ident.startswith(':' + node + '_') for node in nodes)

    def permitted(row):
        if row.tag == 'tlLogic':
            return row.get('id') in controllers
        if row.tag == 'edge':
            return internal(row.get('id')) or row.get('from') in nodes or row.get('to') in nodes
        if row.tag == 'junction':
            return row.get('id') in nodes or internal(row.get('id'))
        if row.tag == 'connection':
            edge = roads.get(row.get('from'))
            return internal(row.get('from')) or (edge is not None and edge.get('to') in nodes)
        return False

    def key(row):
        return ((row.get('from'), row.get('to'), row.get('fromLane'), row.get('toLane'))
                if row.tag == 'connection' else row.get('id', row.tag))

    def canonical(row):
        return (dict(row.attrib), [canonical(child) for child in row]) if row is not None else None

    changes, outside = [], []
    for tag in sorted({row.tag for row in original} | {row.tag for row in candidate}):
        left = {key(row):row for row in original if row.tag == tag}
        right = {key(row):row for row in candidate if row.tag == tag}
        for ident in sorted(left.keys() | right.keys()):
            a, b = left.get(ident), right.get(ident)
            if canonical(a) == canonical(b):
                continue
            change = {'kind': tag, 'id': ident, 'change': 'added' if a is None else 'removed' if b is None else 'updated'}
            changes.append(change)
            if any(not permitted(row) for row in [a, b] if row is not None):
                outside.append(change)
    # A local rebuild may alter the nearby lane geometry. It cannot silently
    # change speed, permissions, friction, lane count or other lane semantics.
    semantics = []
    for ident in sorted(roads.keys() & new_roads.keys()):
        a = {lane.get('id'):{k:v for k,v in lane.attrib.items() if k not in ['shape', 'length']}
             for lane in roads[ident].findall('lane')}
        b = {lane.get('id'):{k:v for k,v in lane.attrib.items() if k not in ['shape', 'length']}
             for lane in new_roads[ident].findall('lane')}
        if a != b:
            semantics.append(ident)
    removed = sorted(roads.keys() - new_roads.keys())
    added = sorted(new_roads.keys() - roads.keys())
    return {'outside_scope_changes': outside, 'changes': changes,
        'changed_normal_lane_semantics': semantics, 'removed_normal_roads': removed,
        'new_normal_roads': added,
        'passes': not outside and not semantics and not added and removed == sorted(removed_roads)}
