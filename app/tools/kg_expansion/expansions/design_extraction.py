from app.tools.kg_expansion.expansions.abstract_expansion import AbstractExpansion
from app.graph.utility.model.model import model
from app.tools.aligner import aligner

nv_has_sequence = model.identifiers.predicates.has_sequence
nv_synonym = str(model.identifiers.objects.synonym)
nv_promoter = str(model.identifiers.objects.promoter)
nv_cds = str(model.identifiers.objects.cds)
nv_dna = str(model.identifiers.objects.dna)
nv_activation = str(model.identifiers.objects.activation)

# These are interactions within a design which 
# are specific to the design for example, a cds 
# downstream of a promoter.
s_interactions = {
    nv_activation : [{nv_promoter,nv_cds},
                     {nv_promoter,nv_dna}]
}
class TruthDesignExtraction(AbstractExpansion):
    '''
    Extracts information from designs within the world graph.
    '''
    def __init__(self, truth_graph, miner):
        super().__init__(truth_graph, miner)
    
    def expand(self):
        self.integrate_design(self._wg.get_design_names())

    def integrate_design(self,graph_name):
        if not isinstance(graph_name,list):
            graph_name = [graph_name]
        if len(graph_name) == 0:
            return
        
        d_graph = self._wg.get_design(graph_name)
        entities = d_graph.get_physicalentity()

        i_graph = self._tg.interactions.get()
        t_pes = self._tg.get_physicalentity()
        seen_interactions = []
        integated_entities = []
        for o_entity in entities:
            entity = self._resolve_entity(o_entity,t_pes)
            if not entity.is_equal(o_entity):
                self._tg.synonyms.positive(entity,o_entity.get_key())
            if len(d_graph.get_haspart(entity)) == 0:
                integated_entities.append(entity)
            for interaction in d_graph.get_interactions(o_entity):
                res_entities = []
                interaction = interaction.n
                if interaction in seen_interactions:
                    continue
                seen_interactions.append(interaction)
                i_eles = d_graph.get_interaction_elements(interaction)
                if self._is_design_specific(interaction,i_eles):
                    continue
                for i_e in i_eles:
                    part = self._resolve_entity(i_e.v,t_pes)
                    res_entities.append((part,i_e.get_type()))

                # Check if interaction exists.
                for o_i in i_graph.interactions(participant=entity.get_key()):
                    if o_i.get_type() != interaction.get_type():
                        continue
                    e_ints = [(i.v,i.get_type()) for 
                               i in i_graph.interactions(o_i)]
                    if len(list(set(res_entities) - set(e_ints))) == 0:
                        interaction = o_i
                        res_entities = e_ints
                        break
                for part in res_entities:
                    self._tg.interactions.positive(interaction,part[0],
                                                   part[1])
        seens = []
        for ie in integated_entities:
            for ie1 in integated_entities:
                if ie == ie1:
                    continue
                if (ie,ie1) in seens:
                    continue
                seens.append((ie,ie1))
                self._tg.usage.positive(ie,ie1)



    def _is_design_specific(self,interaction,elements):
        i_type = interaction.get_type()
        if i_type in s_interactions:
            p_combs = s_interactions[i_type]
            elements = {e.v.get_type() for e in elements}
            if elements in p_combs:
                return True
        return False

    def _resolve_entity(self,entity,t_pes):
        res = self._tg.node_query(entity)
        if len(res) != 0:
            assert(len(res) == 1)
            res = res[0]
            # 2. Entity is a synonym.
            if res.get_type() == nv_synonym:
                syn = self._tg.synonyms.get(synonym=res)
                syn = list(syn.synonyms(synonym=res))
                assert(len(syn) == 1)
                return syn[0].n
            # 1. Entity is directly in the network.
            return res
        if hasattr(entity,"hasSequence"):
            seq_props = {nv_has_sequence : entity.hasSequence.upper()}
            res = self._tg.node_query(**seq_props)
            if len(res) != 0:
                # 3. Entity has a direct sequence match in the network.
                assert(len(res) == 1)
                return res[0]
        qti = {"name" : self._get_name(entity.get_key())}
        results = list(self._tg.query_text_index(qti,fuzzy=True))
        if len(results) > 0:
            # 4. Fuzzy String match & semantic type match
            for r in results:
                if r.get_type() == entity.get_type():
                    return r
        if hasattr(entity,"hasSequence"):
            d_seq = entity.hasSequence.upper()
            d_seq_len = len(d_seq)
            highest_score = [0,None]
            for t_entity in t_pes:
                if hasattr(t_entity,"hasSequence"):
                    t_seq = t_entity.hasSequence.upper()
                    if aligner.string_length_diff(d_seq_len,len(t_seq)):
                        continue
                    score = int(aligner.sequence_match(d_seq,t_seq)*100)
                    if score > highest_score[0]:
                        highest_score = [score,t_entity]
            if highest_score[0] > self._match_threshold:
                # 5. Partial Sequence Match
                return highest_score[1]
        # 6. Entity not in the network.
        return entity
        