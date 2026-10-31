"""Contract interior normal roads without changing the operator timetable."""
import copy


def contract_reference(reference, removed_roads, *, network_sha256):
    updated = copy.deepcopy(reference)
    for direction in updated['directions'].values():
        original = direction['path']
        indices = {index:index - sum(edge in removed_roads for edge in original[:index])
                   for index in range(len(original))}
        for row in [direction, *direction['trips']]:
            row['path'] = [edge for edge in row['path'] if edge not in removed_roads]
            for stop in row['stops']:
                if stop['edge'] in removed_roads:
                    raise ValueError('A served stop lies on a removed road; rematch and review its actual berth')
                # A short working retains canonical direction indices, even
                # when its own route starts after the removed junction road.
                stop['path_index'] = indices[stop['path_index']]
    updated['network_sha256'] = network_sha256
    return updated
