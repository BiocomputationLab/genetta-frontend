from app.graph.utility.model.model import model
from app.tools.graph_query.datatype_handlers.abstract_handler import AbstractHandler

p_description = model.identifiers.external.description
class MetadataHandler(AbstractHandler):
    def __init__(self,graph):
        super().__init__(graph)

    def get_name(self):
        return "Metadata"
    
    def get_description(self):
        return "Returns entities based on matches within metadata."
    
    def get_example(self):
        return "Repression"
    
    def handle(self,query,strict=False):
        results = {}
        qry_eles = self._miner.get_entities(query)
        e_res = []
        entities = self._identify_entities(qry_eles,index=p_description,
                                           predicate="AND",threshold=1,
                                           strict=strict)
        for entity,score in entities.items():
            d = f'{entity.name} - {self._get_name(entity.get_type())}'
            e_res.append((score, 
                         {"description" : d, 
                          "entity" : entity.get_key()}))
            results[None] = e_res
        return results


    def feedback(self, source, result, positive=True):
        pass