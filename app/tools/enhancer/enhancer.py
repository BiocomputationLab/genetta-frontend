import os
from app.tools.data_miner.data_miner import DataMiner
from app.tools.enhancer.enhancements.design_enhancements import DesignEnhancements
from app.tools.enhancer.enhancements.truth_enhancements import TruthEnhancements
tg_initial_fn = os.path.join(os.path.dirname(os.path.realpath(__file__)),"seeder","tg_initial.json")

class Enhancer:
    def __init__(self,graph):
        self._graph = graph
        self._miner = DataMiner()
        self._enhancements = DesignEnhancements(self._graph,self._miner)
    
    def get_canonical_entity(self,entity,gn):
        print("get_canonical_entity not implemented.")
        return {}

    # --- Design ---
    def enhance_design(self,graph_name,mode="automated"):
        return self._design_enhancements.enhance(graph_name,mode=mode)
    
    def apply_design(self,replacements,graph_name,feedback=None):
        return self._design_enhancements.apply(replacements,graph_name,feedback=feedback)

