from app.tools.enhancer.enhancements.abstract_enhancements import AbstractEnhancement
from app.tools.enhancer.enhancements.interaction.protein_production import TruthProteinProduction

class TruthEnhancements(AbstractEnhancement):
    def __init__(self,world_graph,miner):
        super().__init__(world_graph,miner,[TruthProteinProduction])
        
    def enhance(self):
        res = {}
        if len(self._enhancers) == 0:
            return res
        for evaluator in self._enhancers:
            res[evaluator.name] = evaluator.enhance()
        return res