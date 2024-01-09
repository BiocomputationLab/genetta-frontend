import os
from app.tools.data_miner.data_miner import data_miner
from app.tools.kg_expansion.expansions.derivative import TruthInteractionDerivative
from app.tools.kg_expansion.expansions.protein_production import TruthProteinProduction
from app.tools.kg_expansion.expansions.topological_interaction import TruthTopologicalInteraction
from app.tools.kg_expansion.expansions.name_synonym import TruthNameSynonym
from app.tools.kg_expansion.expansions.modules import TruthModules
from app.tools.kg_expansion.expansions.identify_derivative import TruthDerivative

tg_initial_fn = os.path.join(os.path.dirname(os.path.realpath(__file__)),"seeder","tg_initial.json")
# For some reason module is breaking when running not in isolation.
# Check if its still broken without the NameSynonym || PP Expan
class TruthGraphBuilder:
    def __init__(self,graph):
        self._graph = graph
        self._miner = data_miner
        self._modules = [#TruthDerivative(self._graph.truth,
                         #                self._miner),
                         TruthInteractionDerivative(self._graph.truth,
                                                self._miner),
                         #TruthProteinProduction(self._graph.truth,
                         #                       self._miner),
                         TruthNameSynonym(self._graph.truth,
                                                self._miner),
                         TruthModules(self._graph.truth,
                                                self._miner),
                         TruthTopologicalInteraction(self._graph.truth,
                                                self._miner),
                                                ]
    
    def seed(self):
        '''
        Keep it seperate because it should only need 
        to be loaded once ever.
        '''
        from app.tools.kg_expansion.seeder.seeder import Seeder
        if os.path.isfile(tg_initial_fn):
            print("Truth Graph present, building from file.")
            self._graph.truth.drop()
            self._graph.truth.load(tg_initial_fn)
        else:
            self._graph.truth.drop()
            seeder = Seeder(self._graph.truth,self._miner)
            seeder.enable_all()
            seeder.build()
            self._graph.truth.save(tg_initial_fn)
    
    def expand(self):
        for mod in self._modules:
            mod.expand()

