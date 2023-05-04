from app.tools.evaluator.abstract_evaluator import AbstractEvaluator
from app.tools.evaluator.standard.referential import ReferentialEvaluator
from app.tools.evaluator.standard.derived_type import TypeEvaluator

class StandardEvaluator(AbstractEvaluator):
    '''
    Evaluates a design for standard elements.
    '''
    def __init__(self, world_graph, miner):
        super().__init__(world_graph, miner, evaluators=[ReferentialEvaluator,TypeEvaluator])

