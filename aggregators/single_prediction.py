import pickle
import pandas as pd
from utils.anchor_parser import anchor_parser
from pymongo import MongoClient

def get_single_pred_info(index):

    target = "quality"
    dataset_name = "white-wine"
    model_name = "rf"

    with open('./model/selected-{}.pickle'.format(model_name), 'rb') as f:
        model = pickle.load(f)

    client = MongoClient("localhost", 27017)
    db = client["pipeline"]

    data_meta_collection = db["data"]
    datapoint_collection = db["datapoint"]
    model_collection = db["model"]
    model_scores_collection = db["model_scores"]
    anchor_meta_collection = db["anchor_meta"]
    anchor_collection = db["anchor"]
    shap_meta_collection = db["shap_meta"]
    shap_collection = db["shap"]
    trustscore_meta_collection = db["trustscore_meta"]
    trustscore_collection = db["trustscore"]

    data_meta = data_meta_collection.find_one({"type": "test", "name": dataset_name})

    feature_names = data_meta["features"]
    classes = data_meta["classes"]

    datapoint = datapoint_collection.find_one({"data_id": data_meta["_id"], "index": index})

    datapoint_df = pd.DataFrame([datapoint["values"]], columns=feature_names).drop(columns=target)

    model_pred = model.predict(datapoint_df)
    model_pred_proba = model.predict_proba(datapoint_df)
    probas = dict(zip([str(x) for x in classes], model_pred_proba[0]))

    model_meta = model_collection.find_one({"stage": "selection", "model_name": model_name})
    model_scores = model_scores_collection.find_one({"model_id": model_meta["_id"]})
    anchor_meta = anchor_meta_collection.find_one({"model_id": model_meta["_id"]})
    anchor = anchor_collection.find_one({"anchor_meta_id": anchor_meta["_id"], "index": index})
    shap_meta = shap_meta_collection.find_one({"model_id": model_meta["_id"]})
    shap = shap_collection.find_one({"shap_meta_id": shap_meta["_id"], "index": index, "class": int(model_pred[0])})
    trustscore_meta = trustscore_meta_collection.find_one({"model_id": model_meta["_id"]})
    trustscore = trustscore_collection.find_one({"trustscores_meta_id": trustscore_meta["_id"], "index": index})

    dp = datapoint_df.to_dict("records")[0]

    anchor_precision = anchor["precision"]
    anchor_coverage = anchor["coverage"]
    my_anchors = [anchor_parser(elem) for elem in anchor["anchor"]]

    shap_values = dict(zip(feature_names, shap["values"]))

    ts_stats = trustscore_meta["statistics"]
    ts = trustscore["score"]
    ts_neighbour = trustscore["neighbour"]
    ts_is_outlier = trustscore["extreme"]

    explanation_dict = {
        "classes": classes,
        "test_scores": {
            "f1": model_scores["general"]["f1"],
            "precision": model_scores["general"]["precision"],
            "recall": model_scores["general"]["recall"],
        },
        "datapoint": dp,
        "prediction": {
            "class": model_pred[0],
            "probas": probas
        },
        "anchor": {
            "rules": my_anchors,
            "precision": anchor_precision,
            "coverage": anchor_coverage,
        },
        "shap": {
            "values": shap_values
        },
        "trustscore": {
            "statistics": ts_stats,
            "score": ts,
            "is_outlier": ts_is_outlier,
            "closest_prediction": ts_neighbour
        }
    }

    return explanation_dict