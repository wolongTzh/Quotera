from typing import NamedTuple
import csv
from rdflib import Graph, URIRef, Namespace, Literal
from rdflib.namespace import RDF
import json
import uuid


# ------ Entity type definitions

class LPitem(NamedTuple):
    entity_id: str
    title: str
    attributes: str


class RIitem(NamedTuple):
    entity_id: str
    title: str
    res_url: str
    res_format: str


class PRitem(NamedTuple):
    entity_id: str
    title: str
    actor: str
    situation: str
    task: str
    plan: str
    expected_result: str


class Relation(NamedTuple):
    head_id: str
    tail_id: str
    relation_type: str


def convert_csv_to_ttl(
        graph_id='test_graph_id',
        entities_csv_path='./data/entities.csv',
        relations_csv_path='./data/relations.csv',
        output_ttl_path='./data/output.ttl'):


    g = Graph()

    # Namespace definitions

    edukg = Namespace('http://edukg.org/ontology#')
    e_ns = Namespace(f'http://edukg.org/graphs/{graph_id}/entities#')
    r_ns = Namespace(f'http://edukg.org/graphs/{graph_id}/relations#')

    g.bind('edukg', edukg)
    g.bind('e', e_ns)
    g.bind('r', r_ns)


    # Read entities
    entity_id_to_uri = {}
    entity_id_to_entity = {}

    with open(entities_csv_path, encoding='utf-8') as f:
        reader = csv.reader(f)
        for row, i in enumerate(reader):
            prefix = f"Entity file row {row + 1} - "

            # Get the entity type
            try:
                i_type = {
                    'LPitem': LPitem,
                    'RIitem': RIitem,
                    'PRitem': PRitem,
                }[i[0]]
            except KeyError:
                raise Exception(prefix + f"Invalid entity type: {i[0]}")
            
            # Check the len of params
            # assert len(i) == {
            #     'LPitem': 4,
            #     'RIitem': 5,
            #     'PRitem': 8,
            # }[i[0]]
            if i[0] == "LPitem":
                i = i_type(*i[1:4])
            elif i[0] == "RIitem":
                i = i_type(*i[1:5])
            elif i[0] == "PRitem":
                i = i_type(*i[1:8])

            # Generate the uri
            try:
                i_uri = URIRef(e_ns + i.entity_id)
            except:
                raise Exception(prefix + f"Invalid entity id: {i.entity_id}")
            if i.entity_id in entity_id_to_uri:
                raise Exception(prefix + f"Duplicated entity id: {i.entity_id}")
            entity_id_to_uri[i.entity_id] = i_uri
            entity_id_to_entity[i.entity_id] = i

            # Add the common attributes
            g.add((i_uri, edukg.title, Literal(i.title)))
            identifier = str(uuid.uuid4())
            g.add((i_uri, edukg.identifier, Literal(identifier)))

            # Add the specific attributes for each entity type
            match i:
                case LPitem():
                    try:
                        json.loads(i.attributes)
                    except json.JSONDecodeError as e:
                        raise Exception(prefix + f"Invalid attributes format for LPitem {i.entity_id}:\n{e}")
                    
                    g.add((i_uri, RDF.type, edukg.LPitem))
                    g.add((i_uri, edukg.contentJson, Literal(i.attributes)))
                
                case RIitem():
                    g.add((i_uri, RDF.type, edukg.RIitem))
                    g.add((i_uri, edukg.resourceUrl, Literal(i.res_url)))
                    g.add((i_uri, edukg.resourceFormat, Literal(i.res_format)))
                
                case PRitem():
                    g.add((i_uri, RDF.type, edukg.PRitem))
                    g.add((i_uri, edukg.actorRole, Literal(i.actor)))
                    g.add((i_uri, edukg.situation, Literal(i.situation)))
                    g.add((i_uri, edukg.task, Literal(i.task)))
                    g.add((i_uri, edukg.actionPlan, Literal(i.plan)))
                    g.add((i_uri, edukg.expectedResult, Literal(i.expected_result)))
            
    # Read relations
    relation_name_to_uri = {}
    with open(relations_csv_path, encoding="utf-8") as f:
        reader = csv.reader(f)

        for row, i in enumerate(reader):
            prefix = f"Relations file row {row + 1} - "
            i = Relation(*i)

            head_id, tail_id = i.head_id, i.tail_id

            # Get the head and tail
            try:
                head = entity_id_to_entity[head_id]
            except KeyError:
                raise Exception(prefix + f"Head id unfound: {head_id}")
            try:
                tail = entity_id_to_entity[tail_id]
            except KeyError:
                raise Exception(prefix + f"Tail id unfound: {tail_id}")

            # Get the relation type
            r_type = i.relation_type
            if not type(head) is type(tail):
                match head, tail:

                    case LPitem(), RIitem():
                        r_type = edukg.hasResource
                    case RIitem(), LPitem():
                        head_id, tail_id = tail_id, head_id
                        r_type = edukg.hasResource

                    case LPitem(), PRitem():
                        head_id, tail_id = tail_id, head_id
                        r_type = edukg.appliesTo
                    case PRitem(), LPitem():
                        r_type = edukg.appliesTo

                    case RIitem(), PRitem():
                        head_id, tail_id = tail_id, head_id
                        r_type = edukg.appliesTo
                    case PRitem(), RIitem():
                        r_type = edukg.appliesTo
            else:
                if type(head) is not LPitem:
                    raise Exception(prefix + "Only LPitem has internal relations.")
                if not r_type:
                    raise Exception(prefix + "Empty relation type")
                
                if r_type not in relation_name_to_uri:
                    try:
                        r_uri = URIRef(r_ns + r_type)
                    except:
                        raise Exception(prefix + f"Invalid relation type: {r_type}")
                    g.add((r_uri, RDF.type, edukg.DisciplinaryProperty))
                    relation_name_to_uri[r_type] = r_uri
                
                r_type = relation_name_to_uri[r_type]
            
            # Add the relation
            # print(head_id, r_type, tail_id)
            g.add((entity_id_to_uri[head_id], r_type, entity_id_to_uri[tail_id]))

    with open(output_ttl_path, 'w') as f:
        f.write(g.serialize(format='turtle'))


if __name__ == '__main__':
    convert_csv_to_ttl(entities_csv_path="entities.csv", relations_csv_path="relations.csv", output_ttl_path="output.ttl")
