"""Visual context and native vehicle coverage for the complete line."""
def edges(net,reference):
    route=set(e for direction in reference['directions'].values() for e in direction['path'])
    capture=set(route);scene=set(route)
    for ident in route:
        edge=net.getEdge(ident)
        for node in [edge.getFromNode(),edge.getToNode()]:
            capture.update(e.getID() for e in node.getIncoming()+node.getOutgoing())
    for direction in reference['directions'].values():
        for stop in direction['stops']:
            scene.update(e.getID() for e,_ in net.getNeighboringEdges(*stop['point'],150,includeJunctions=False))
    scene.update(capture)
    return sorted(capture),sorted(scene)

def selection(net,reference,target,network_file):
    import xml.etree.ElementTree as ET
    capture,_=edges(net,reference);wanted=set(capture)
    nodes={getattr(net.getEdge(e),method)().getID() for e in capture for method in ['getFromNode','getToNode']}
    # Internal connections belong to the adjacent junction, not a separate road.
    for node in ET.parse(network_file).getroot().findall('junction'):
        if node.get('id') in nodes:
            wanted.update(lane.rsplit('_',1)[0] for lane in node.get('intLanes','').split())
    target.write_text(''.join('edge:'+edge+'\n' for edge in sorted(wanted)))
    return capture
