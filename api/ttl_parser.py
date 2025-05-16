from rdflib import Graph, URIRef, Literal
import json



nodes = {}
links = []

def simplify_uri(uri):
    if "#" in uri:
        return uri.split("#")[-1]
    elif "/" in uri:
        return uri.split("/")[-1]

def check_if_node(uri):
    if "relation" in uri:
        return False
    return True

def gen_json_from_ttl(ttl_path):  
    # 载入 TTL 文件
    g = Graph()
    g.parse(ttl_path, format="ttl")
    for s, p, o in g:
        # print(s, p, o)
        s_id = str(s)
        o_id = str(o)
        p_label = simplify_uri(str(p))

        if s_id not in nodes and check_if_node(s_id):
            nodes[s_id] = {"id": s_id, "name": simplify_uri(s_id)}

        if "http://edukg.org/graphs/" in o_id:        
            p_label = p.split("#")[-1]
            print(p_label)
            if o_id not in nodes and check_if_node(o_id):
                nodes[o_id] = {"id": o_id, "name": simplify_uri(o_id)}    
            links.append({
                "source": s_id,
                "target": o_id,
                "relation": p_label
            })
        if p_label == "title":
            nodes[s_id]["name"] = str(o)
        if simplify_uri(str(p)) == "type" and check_if_node(s_id):
            # print(o)
            nodes[s_id]["type"] = simplify_uri(str(o))

    graph_data = {
        "graph":{
            "nodes": list(nodes.values()),
            "links": links
        }
    }
    return graph_data
    # for link in graph_data["physics"]["links"]:
    #     head = link["source"]
    #     tail = link["target"]
    #     first = False
    #     sec = False
    #     for node in graph_data["physics"]["nodes"]:
    #         if head == node["id"]:
    #             first = True
    #         if tail == node["id"]:
    #             sec = True
    #     if not first:
    #         print(head)
    #     if not sec:
    #         print(tail)
if __name__ == '__main__':
    ttl_path = "/home/tz/cui/Quotera/api/49827fc0-2916-4d2e-919d-7214b27993af-graph.ttl"
    print(gen_json_from_ttl(ttl_path))