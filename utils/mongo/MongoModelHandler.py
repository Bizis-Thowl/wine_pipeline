from pymongo import MongoClient


class MongoModelHandler():

    def __init__(self, stage, model_name, port=27017):
        # Create a MongoClient to the running mongod instance
        self.client = MongoClient("localhost", port)

        # Get a reference to a particular database
        self.db = self.client["pipeline"]
        self.model_collection = self.db["model"]
        self.model_scores_collection = self.db["model_scores"]
        self.train_process_collection = self.db["train_process"]
        self.train_config_collection = self.db["train_config"]

        self.stage = stage
        self.model_name = model_name

    def store_model(self, clf):

        pipeline_steps = []
        for step in clf.get_params()["steps"]:
            step_type = step[0]
            step_approach = step[1]
            pipeline_steps.append({"type": step_type, "approach": str(step_approach)})

        self.model_collection.insert_one(
            {"stage": self.stage, "model_name": self.model_name, "pipeline": pipeline_steps, "location": ""}
        )

    def store_model_scores(self, general, conf_matrix_train, conf_matrix_test, learning_curve) -> None:

        model_id = self._get_model_id()

        formatted_conf_mat_train = self._format_conf_matrix(conf_matrix_train)
        formatted_conf_mat_test = self._format_conf_matrix(conf_matrix_test)


        self.model_scores_collection.insert_one(
            {
                "model_id": model_id,
                "general": general,
                "confusion_matrices": {"train": formatted_conf_mat_train, "test": formatted_conf_mat_test},
                "learning_curve": learning_curve,
            }
        )

    def _format_conf_matrix(self, df) -> list:
        formatted_mat = []
        for row in df.to_dict("records"):
            formatted_mat.append({str(key): int(value) for key, value in row.items()})
        
        return formatted_mat

    def store_train_process(self, strategies, approach: str, metric: str) -> None:
        
        model_id = self._get_model_id()

        formatted_strategies = self._format_strategies(strategies=strategies)

        self.train_process_collection.insert_one(
            {
                "model_id": model_id,
                "strategies": formatted_strategies,
                "approach": approach,
                "optimization_metric": metric,
            }
        )

    def _format_strategies(self, strategies):
        formatted_strategies = []

        for pipeline_type, options in strategies.items():
            options_formatted = []
            for option in options:
                options_formatted.append(str(option))
            formatted_strategies.append({"type": pipeline_type, "options": options_formatted})
        
        return formatted_strategies

    def store_train_configs(self, results):

        model_id = self._get_model_id()
        train_process_id = self.train_process_collection.find_one({"model_id": model_id})["_id"]

        mean_fit_time = results["mean_fit_time"]
        std_fit_time = results["std_fit_time"]
        mean_score_time = results["mean_score_time"]
        std_score_time = results["std_score_time"]
        params = results["params"]
        mean_test_score = results["mean_test_score"]
        std_test_score = results["std_test_score"]
        rank_test_score = results["rank_test_score"]
        for i, _ in enumerate(mean_fit_time):
            timers = {
                "mean_fit_time": mean_fit_time[i],
                "std_fit_time": std_fit_time[i],
                "mean_score_time": mean_score_time[i],
                "std_score_time": std_score_time[i],
            }
            parameters = {str(key): str(value) for key, value in params[i].items()}
            scores = {
                "mean_test_score": mean_test_score[i],
                "std_test_score": std_test_score[i],
            }
            rank = int(rank_test_score[i])

            self.train_config_collection.insert_one(
                {
                    "train_process_id": train_process_id,
                    "timers": timers,
                    "parameters": parameters,
                    "scores": scores,
                    "rank": rank,
                }
            )

    def _get_model_id(self):
        model_id = self.model_collection.find_one({"stage": self.stage, "model_name": self.model_name})["_id"]
        return model_id