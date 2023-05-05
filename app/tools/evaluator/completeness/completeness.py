from app.tools.evaluator.abstract_evaluator import AbstractEvaluator
from app.tools.evaluator.completeness.hierarchy import HierarchyEvaluator
from app.tools.evaluator.completeness.interaction import InteractionEvaluator
from app.tools.evaluator.completeness.sequence import SequenceEvaluator


class CompletenessEvaluator(AbstractEvaluator):
    '''
    Evaluates how complete a design is, i.e. different datatypes are fully encoded.
    '''
    def __init__(self, world_graph, miner):
        super().__init__(world_graph, miner, evaluators=[
            SequenceEvaluator, HierarchyEvaluator, InteractionEvaluator])
