from app.tools.graph_query.datatype_handlers.abstract_handler import AbstractHandler


class CanonicalHandler(AbstractHandler):
    def __init__(self, graph):
        super().__init__(graph)

    def get_name(self):
        return "Canonical"

    def get_description(self):
        return "Returns the canonical version of a genetic part"

    def get_example(self):
        return "pTet"

    def handle(self, query,strict=False):
        results = {}
        s_graph = self._graph.synonyms.get(threshold=0)
        for qry_ele in self._miner.get_entities(query):
            for entity in self._identify_entities(qry_ele,s_graph,
                                                  strict=strict):
                e_res = []
                if len(list(s_graph.synonyms(canonical=entity))) > 0:
                    # The input entity is the canonical.
                    desc = f'{self._get_name(entity.get_key())} is canonical.'
                    e_res = [(100, {"description" : desc, 
                                    "entity" : entity.get_key()})]
                else:
                    for syn in s_graph.synonyms(synonym=entity):
                        desc = self._get_name(syn.n.get_key())
                        e_res.append((syn.confidence,
                                      {"description" : desc, 
                                       "entity" : syn.n.get_key()}))
                if len(e_res) > 0:
                    # The query value is considered the source 
                    # opposed to the entity with synonyms because
                    # its more valuable to take direct user input 
                    # opposed to reinforcing existing knowledge. 
                    if qry_ele in results:
                        e_res = self._merge_duplicates(results[qry_ele],e_res)
                    e_res = self._rank_result(e_res)
                    results[qry_ele] = e_res
        return results

    def feedback(self, source, result, positive=True):
        if positive:
            self._graph.synonyms.positive(result,source)
        else:
            self._graph.synonyms.negative(result,source)