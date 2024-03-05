from app.tools.kg_expansion.expansions.abstract_expansion import AbstractExpansion
from app.graph.utility.model.model import model

class TruthTopologicalInteraction(AbstractExpansion):
    '''
    Extracts information from designs within the world graph.
    '''
    def __init__(self, truth_graph, miner):
        super().__init__(truth_graph, miner)
    
    def expand(self):
        '''
        Infers missing interaction edges from 
        pre-defined shapes commonly encountered.
        '''
        m_graph = self._tg.modules.get()
        for modules in m_graph.modules():
            pass
