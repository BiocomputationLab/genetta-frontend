from app.tools.evaluator.abstract_evaluator import AbstractEvaluator
from app.tools.evaluator.completeness.completeness import CompletenessEvaluator
from app.tools.evaluator.standard.standard import StandardEvaluator
from app.tools.data_miner.data_miner import DataMiner

class Evaluator(AbstractEvaluator):
    def __init__(self, world_graph):
        super().__init__(world_graph, DataMiner(), evaluators=[CompletenessEvaluator,
                                                         StandardEvaluator])

    def get_evaluators(self):
        evaluators = []
        def ge(evaluator):
            for e in evaluator:
                evaluators.append(e)
                ge(e)
        ge(self)
        return evaluators
    
    def evaluate(self, graph_name,flatten=False):
        dg = self._wg.get_design(graph_name)
        feedback = super().evaluate(dg)
        if not flatten:
            return feedback

        def _flatten(d):
            comments = {}
            if "comments" in d:
                comments = d["comments"]
            if "evaluators" in d:
                for k, v in d["evaluators"].items():
                    if isinstance(v, dict):
                        comments.update(_flatten(v))
            return comments
        for k,v in feedback["evaluators"].items():
            for k1,v1 in v["evaluators"].items():
                feedback["evaluators"][k]["evaluators"][k1]["comments"] = _flatten(v1)        
        return feedback
