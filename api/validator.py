from io import BytesIO
import json
import re

from rdflib import Graph, Namespace
from rdflib.namespace import RDF


EDUKG = Namespace("http://edukg.org/ontology#")
GUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
ENTITY_CLASSES = {EDUKG.LPitem, EDUKG.RIitem, EDUKG.PRitem, EDUKG.LearningPointCollection}


def validate_turtle(file_bytes: bytes) -> dict:
    """Parse an uploaded file as Turtle and return a JSON-safe result."""
    if not file_bytes:
        return {
            "valid": False,
            "stage": "input",
            "message": "Uploaded file is empty.",
            "triple_count": 0,
        }

    graph = Graph()
    try:
        graph.parse(source=BytesIO(file_bytes), format="turtle")
    except Exception as exc:
        return {
            "valid": False,
            "stage": "syntax",
            "message": f"Invalid Turtle syntax: {exc}",
            "triple_count": 0,
        }

    if len(graph) == 0:
        return {
            "valid": False,
            "stage": "syntax",
            "message": "The Turtle file contains no RDF triples.",
            "triple_count": 0,
        }

    errors = []
    entities = set()
    for entity_class in ENTITY_CLASSES:
        entities.update(graph.subjects(RDF.type, entity_class))

    for entity in entities:
        titles = list(graph.objects(entity, EDUKG.title))
        identifiers = list(graph.objects(entity, EDUKG.identifier))
        if len(titles) != 1 or not str(titles[0]).strip():
            errors.append(f"{entity}: exactly one non-empty edukg:title is required")
        if len(identifiers) != 1 or not GUID_RE.fullmatch(str(identifiers[0])):
            errors.append(f"{entity}: edukg:identifier must be a valid GUID")

        for content in graph.objects(entity, EDUKG.contentJson):
            try:
                value = json.loads(str(content))
            except json.JSONDecodeError as exc:
                errors.append(f"{entity}: contentJson is not valid JSON ({exc.msg})")
                continue
            if not isinstance(value, list) or any(
                not isinstance(item, dict)
                or set(item) - {"predicate", "value"}
                or not isinstance(item.get("predicate"), str)
                or "value" not in item
                for item in value
            ):
                errors.append(f"{entity}: contentJson must be a list of {{predicate, value}} objects")

    # Custom relationship resources must be object properties between LPitems.
    disciplinary_properties = set(graph.subjects(RDF.type, EDUKG.DisciplinaryProperty))
    for predicate in disciplinary_properties | {EDUKG.hasChild, EDUKG.hasParent}:
        for subject, _, obj in graph.triples((None, predicate, None)):
            if not any(graph.objects(subject, RDF.type)):
                errors.append(f"{subject}: relationship subject has no rdf:type")
            if not (obj, RDF.type, EDUKG.LPitem) in graph:
                errors.append(f"{predicate}: relationship object {obj} is not an edukg:LPitem")

    # A custom type resource used by rdf:type should itself be declared as LPitem.
    for _, _, type_resource in graph.triples((None, RDF.type, None)):
        if str(type_resource).startswith("http://edukg.org/graphs/") and type_resource not in entities:
            if (type_resource, RDF.type, EDUKG.LPitem) not in graph:
                errors.append(f"Type resource {type_resource} must be declared as edukg:LPitem")

    if errors:
        return {
            "valid": False,
            "stage": "structure",
            "message": f"EduKG structure validation failed ({len(errors)} error(s)).",
            "triple_count": len(graph),
            "errors": errors,
        }

    return {
        "valid": True,
        "stage": "structure",
        "message": f"Valid Turtle syntax and EduKG structure ({len(graph)} RDF triples).",
        "triple_count": len(graph),
        "errors": [],
    }
