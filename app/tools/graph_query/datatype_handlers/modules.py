from app.tools.graph_query.datatype_handlers.abstract_handler import AbstractHandler
from app.graph.utility.model.model import model

nv_physical_entity = model.identifiers.objects.physicalentity
nv_pe_cc = model.get_class_code(nv_physical_entity)
class ModuleHandler(AbstractHandler):
    def __init__(self,graph):
        super().__init__(graph)

    def get_name(self):
        return "Module"
    
    def get_description(self):
        return "Returns functional modules that contain an entity."
    
    def get_example(self):
        return "pAmtR"
    
    def handle(self,query):
        results = {}
        graph = self._graph.modules.get(threshold=0)
        graph += self._graph.synonyms.get(threshold=0)
        graph += self._graph.interactions.get(threshold=0)
        for qry_ele in self._miner.get_entities(query):
            entities = self._identify_entities(qry_ele,graph)
            entities = self._cast_synonyms(entities,graph)
            for entity in entities:
                e_res = []
                if model.is_derived(entity.get_type(),nv_pe_cc):
                    interactions = graph.interactions(participant=entity)
                for i in interactions:
                    modules = graph.modules(object = i)
                for m in modules:
                    m_ints = graph.modules(m.n)
                    conf = 0
                    description = ""
                    for mi in m_ints:
                        conf += mi.confidence
                        description += f"{mi.v.name}-"
                    conf = int(conf / len(m_ints))
                    e_res.append((conf,{"description" : description, 
                                        "entity" : m.n.get_key()}))
                if len(e_res) > 0:
                    entity = entity.get_key()
                    if entity in results:
                        e_res = self._merge_duplicates(results[entity],e_res)
                    e_res = self._rank_result(e_res)
                    results[entity] = e_res
        return results

    def feedback(self, source, result, positive=True):
        print(source,result)
        graph = self._graph.modules.get(result)
        # We assume source is already an edge.
        for e in graph.edges():
            print(e)
            if positive:
                self._graph.modules.positive(e.n,e.v,e.get_type())
            else:
                self._graph.modules.negative(e.n,e.v,e.get_type())