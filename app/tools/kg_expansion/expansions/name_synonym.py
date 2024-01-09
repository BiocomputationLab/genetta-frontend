from app.tools.kg_expansion.expansions.abstract_expansion import AbstractExpansion
from app.graph.utility.model.model import model

nv_dna = str(model.identifiers.objects.dna)
nv_dna_cc = model.get_class_code(nv_dna)
nv_activated = str(model.identifiers.predicates.activated)
nv_modifier = str(model.identifiers.predicates.modifier)
nv_product = str(model.identifiers.predicates.product)
nv_repressed = str(model.identifiers.predicates.repressed)
nv_template = str(model.identifiers.predicates.template)

bl_ints = [nv_activated,nv_modifier,
           nv_product,nv_repressed,
           nv_template]

class TruthNameSynonym(AbstractExpansion):
    def __init__(self, truth_graph, miner):
        super().__init__(truth_graph, miner)

    def expand(self):
        '''
        For each physcial entity, set a synonym node 
        with the name of the entity as value.
        If multiple nodes have the same name, 
        share the confidence.
        '''
        name_map = {}
        s_graph = self._tg.synonyms.get()
        i_graph = self._tg.interactions.get()
        for entity in self._tg.get_physicalentity():
            try:
                e_synonyms = [s.v.get_key() for s in s_graph.synonyms(entity)]
            except ValueError:
                e_synonyms = []
            for n_synonym in self._generate_synonyms(entity,i_graph):
                if n_synonym in e_synonyms:
                    continue
                if n_synonym in name_map:
                    name_map[n_synonym].append(entity)
                else:
                    name_map[n_synonym] = [entity]

        for name,entities in name_map.items():
            conf = int(100/len(entities))
            for entity in entities:
                self._tg.synonyms.positive(entity,name,score=conf)

    def _generate_synonyms(self,entity,i_graph):
        synonyms = []
        e_key = entity.get_key()
        e_name = self._get_name(e_key)
        synonyms.append(e_name)
        e_type = self._get_name(entity.get_type()).lower()
        if e_type not in e_name.lower():
            synonyms.append(f'{e_name}_{e_type}')
        try:
            ints = list(i_graph.interactions(participant=e_key))
        except ValueError:
            ints = []
        for i in ints:
            if i.get_type() in bl_ints:
                continue
            part_t = [i for i in i_graph.interactions(i.get_key()) 
                      if i.v == entity]
            assert(len(part_t) == 1)
            part_name = self._get_name(part_t[0].get_type())
            synonyms.append(f'{e_name}_{part_name.lower()}')
        return synonyms
