import pymongo
import json
from bson.json_util import dumps

def analyze_collections(db):
    collection_structure = {}
    for collection_name in db.list_collection_names():
        sample_doc = db[collection_name].find_one()
        if sample_doc:
            collection_structure[collection_name] = {
                "attributes": analyze_document(sample_doc),
                "description": ""
            }
    return collection_structure

def analyze_document(document):
    doc_structure = {}
    for key, value in document.items():
        doc_structure[key] = type(value).__name__
    return doc_structure

def analyze_relations(db, collection_structure):
    relations = {}
    for collection_name, struc in collection_structure.items():
        structure = struc["attributes"]
        foreign_keys = []
        for field, datatype in structure.items():
            if datatype == 'ObjectId':
                # check if field references to another collection
                ref_collection = field[:-3]  # assuming field name is something like 'user_id'
                if ref_collection in db.list_collection_names():
                    foreign_keys.append({
                        'field': field,
                        'references': ref_collection
                    })
        if foreign_keys:
            relations[collection_name] = foreign_keys
    return relations

def main():
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["pipeline"]

    collection_structure = analyze_collections(db)
    relations = analyze_relations(db, collection_structure)

    db_structure = {
        'collections': collection_structure,
        'relations': relations
    }

    with open('db_structure.json', 'w') as f:
        f.write(dumps(db_structure, indent=2))

if __name__ == '__main__':
    main()
