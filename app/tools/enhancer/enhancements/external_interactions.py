from app.tools.enhancer.enhancements.abstract_enhancements import AbstractEnhancement
from app.graph.utility.model.model import model

class ExternalInteractions(AbstractEnhancement):
    '''
    Searches and pull any external interactions into 
    the design graph for cases where entities 
    are not in truth graph. 
    '''
    def __init__(self, world_graph, miner):
        super().__init__(world_graph, miner)

    def enhance(self,graph_name,automated=False):
        '''     
        Considerations:
            1. Should external and tg processes be merged into one?
        '''
        graph = self._wg.get_design(graph_name)
        changes = {}
        return changes
    
    def apply(self,replacements,graph_name):
        graph = self._wg.get_design(graph_name)



