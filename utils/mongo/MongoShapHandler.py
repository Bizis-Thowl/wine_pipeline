from pymongo import MongoClient


class MongoShapHandler:
    def __init__(self, stage, model_name, port=27017):
        # Create a MongoClient to the running mongod instance
        self.client = MongoClient("localhost", port)

        # Get a reference to a particular database
        self.db = self.client["pipeline"]
        self.model_collection = self.db["model"]
        self.shap_meta_collection = self.db["shap_meta"]
        self.shap_collection = self.db["shap"]

        self.stage = stage
        self.model_name = model_name

    def store_shap_meta(self, expl_loc, classes, features):
        model_id = self._get_model_id()

        self.shap_meta_collection.insert_one(
            {
                "model_id": model_id,
                "expl_loc": expl_loc,
                "classes": classes,
                "features": features,
            }
        )
    
    def store_shap(self, my_class, value_index, values, interactions):
        model_id = self._get_model_id()

        shap_meta_id = self.shap_meta_collection.find_one(
            {"model_id": model_id}
        )["_id"]

        self.shap_collection.insert_one(
            {
                "shap_meta_id": shap_meta_id,
                "class": my_class,
                "index": value_index,
                "values": values,
                "interactions": interactions
            }
        )

    def _get_model_id(self):
        model_id = self.model_collection.find_one(
            {"stage": self.stage, "model_name": self.model_name}
        )["_id"]
        return model_id
