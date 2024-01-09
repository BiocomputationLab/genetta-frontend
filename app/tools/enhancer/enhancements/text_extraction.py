from app.tools.enhancer.enhancements.abstract_enhancements import AbstractEnhancement
from app.graph.utility.model.model import model


class TextExtraction(AbstractEnhancement):
    '''
    To identify any potential interactions 
    from the dg metadata.
    '''
    def __init__(self, world_graph, miner):
        super().__init__(world_graph, miner)
    
    def enhance(self, graph_name, mode="automated"):
        changes = {}
        return changes
        
            
