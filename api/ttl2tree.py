from rdflib import Graph, URIRef, Literal
import json

def simplify_uri(uri):
    if "#" in uri:
        return uri.split("#")[-1]
    elif "/" in uri:
        return uri.split("/")[-1]

def check_if_node(uri):
    if "relation" in uri:
        return False
    return True

def DFS(cur_node, vector, sons, nodes):
    if cur_node in sons:
        for son in sons[cur_node]:
            if son in nodes:
                son_node = nodes[son]
                son_node["children"] = []
                vector.append(son_node)
                DFS(son, son_node["children"], sons, nodes)

def get_tree_json(ttl_path):
    root = ""
    nodes = {}
    sons = {}
    No_rt = False
    rt_ch = []  # two assistant lists to find all the nodes without father
    Has_fa = []

    g = Graph()
    g.parse(ttl_path, format="ttl")

    for s, p, o in g:
        s_id = str(s)
        o_id = str(o)
        p_label = simplify_uri(str(p))

        if "LearningPointCollection" in o_id:
            root = s_id
            sons["S"] = [root]
            break
    
    if root == "":
        No_rt = True
        root = ttl_path.split("/")[-1].split(".")[0]
        sons["S"] = [root]
        sons[root] = []
        nodes[root] = {
            "title": root
        }
        
    for s, p, o in g:
        s_id = str(s)
        o_id = str(o)
        p_label = simplify_uri(str(p))

        if isinstance(o, URIRef) and "hasChild" in p.split("#")[-1] or "contains" in p.split("#")[-1]:
            p_label = p.split("#")[-1]
            if s_id not in sons:
                sons[s_id] = []
            if o_id not in sons[s_id]:
                sons[s_id].append(o_id)
            if s_id not in rt_ch:
                rt_ch.append(s_id)
            if o_id not in Has_fa:
                Has_fa.append(o_id)
        
        elif check_if_node(s_id) and "relation" not in p_label and "22-rdf-syntax-ns#type" not in p_label:
            if s_id not in nodes:
                nodes[s_id] = {
                    "id": s_id
                }
            p_label = p.split("#")[-1]
            if p_label == "type":
                o_id = o_id.split("#")[-1]
            nodes[s_id][p_label] = o_id

    if No_rt:
        for node in rt_ch:
            if node not in Has_fa:
                sons[root].append(node)

    tree_data = {
        "S": []
    }

    DFS("S", tree_data["S"], sons, nodes)

    return tree_data["S"][0]

# if __name__ == "__main__":
#     ttl_path = "sample-physics.ttl"
#     tree_data = get_tree_json(ttl_path)
#     with open("tree_data.json", "w") as f:
#         json.dump(tree_data, f, indent=4)
