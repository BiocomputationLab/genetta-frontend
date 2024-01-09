from app.tools.kg_expansion.expansions.abstract_expansion import AbstractExpansion
from app.graph.utility.model.model import model
nv_ids = model.identifiers

class TruthTextExtraction(AbstractExpansion):
    def __init__(self, truth_graph, miner):
        super().__init__(truth_graph, miner)
        self._interaction_map = {nv_ids.objects.repression : ["repress"],
                                 nv_ids.objects.activation : ["activat"],
                                 nv_ids.objects.binds : ["bind"]}
        self._threshold = 0.85

    def expand(self):
        pes = self._tg.get_physicalentity()
        s_graph = self._tg.synonyms.get()
        for entity in pes:
            if not hasattr(entity,"description"):
                continue
            for desc in entity.description:
                for d_entity in self._miner.get_entities(desc):
                    for interaction,synonyms in self._interaction_map.items():
                        for sim in self._miner.word_similarity(d_entity,synonyms):
                            if sim > self._threshold:
                                print(entity,d_entity,sim) 
                                pass#self._tg.interactions.positive(inter,entity,p_type)
            
