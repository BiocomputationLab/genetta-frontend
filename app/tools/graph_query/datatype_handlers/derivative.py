from app.tools.graph_query.datatype_handlers.abstract_handler import AbstractHandler

class DerivativeHandler(AbstractHandler):
    def __init__(self,graph):
        super().__init__(graph)

    def get_name(self):
        return "Derivative"
    
    def get_description(self):
        return "Returns similar entities to provided genetic parts."

    def get_example(self):
        return "BBa_C0012"
    
    def handle(self,query,strict=False):
        results = {}
        graph = self._graph.derivatives.get(threshold=0)
        graph += self._graph.synonyms.get(threshold=0)
        for qry_ele in self._miner.get_entities(query):
            entities = self._identify_entities(qry_ele,graph,strict=strict)
            entities = self._cast_synonyms(entities,graph)
            for entity in entities:
                e_res = []
                for der in graph.derivatives(entity):
                    desc = f'{self._get_name(der.v.get_key())}'
                    e_res.append((der.confidence, 
                                  {"description" : desc, 
                                    "entity" : der.v.get_key()}))
                if len(e_res) > 0:
                    entity = entity.get_key()
                    if entity in results:
                        e_res = self._merge_duplicates(results[entity],e_res)
                    e_res = self._rank_result(e_res)
                    results[entity] = e_res
        return results


    def feedback(self, source, result, positive=True):
        if positive:
            self._graph.derivatives.positive(source,result)
        else:
            self._graph.derivatives.negative(source,result)