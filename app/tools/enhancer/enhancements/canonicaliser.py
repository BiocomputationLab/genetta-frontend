'''                
Overview of the process:
1. Absolute References
    1.1. Check if an entity name refers directly to a record.
    1.2. Check if the Truth Graph contains a high confidence synonym.
    1.3. Check for a full sequence match.
    1.4. Check metadata for a direct record.
2. Potential References
    2.1. Partial Sequence Match.
    2.1  Mid/Low confidence synonym from Truth Graph.
    2.1. Partial Descriptor From metadata.
3. Post-Processing Score
    3.1. Chance to increase score by comparing entites within the graph.
'''
from app.tools.enhancer.enhancements.abstract_enhancements import AbstractEnhancement
from app.graph.utility.model.model import model
from app.graph.utility.graph_objects.node import Node
from app.tools.aligner import aligner

nv_has_sequence = str(model.identifiers.predicates.has_sequence)
nv_synonym = str(model.identifiers.objects.synonym)
nv_desc = model.identifiers.external.description
class Canonicaliser(AbstractEnhancement):
    def __init__(self, world_graph, miner):
        super().__init__(world_graph, miner)
        self._match_threshold = 80

    def enhance(self,graph_name,automated=True):
        dg = self._wg.get_design(graph_name)
        t_pes = self._wg.truth.get_physicalentity()
        changes = {}
        a_calls = [self._get_truth_absolute,
                   self._get_external_absolute]
        p_calls = [self._get_truth_potential,
                 self._get_external_potential]
        for entity in dg.get_physicalentity():
            e_key = entity.get_key()
            is_canon = False
            if len(dg.get_haspart(entity)) > 0:
                continue # ??
            for c in a_calls:
                res = c(entity,t_pes)
                if res is not None:
                    res,score = res
                    if res.get_key() != e_key:
                        changes[e_key] = [(res,score)]
                    else:
                        is_canon = True
                    break
            if not automated and e_key not in changes and not is_canon:
                results = {}
                for c in p_calls:
                    res = c(entity,t_pes)
                    if len(res) == 0:
                        continue
                    # We let list results continue because 
                    # they are potential changes.
                    for k,v in res.items():
                        if k in res:
                            score = int(max([v,res[k]]))
                        else:
                            score = v
                        results[k] = score
                if len(results) > 0:
                    results = [(k,v) for k,v in results.items()]
                    results.sort(key=lambda x: x[1], reverse=True)
                    changes[e_key] = results
                    
        if automated:
            changes = {k:v[0][0] for k,v in changes.items()}
            return self.apply(changes,graph_name)
        return changes

    def apply(self,replacements,graph_name):
        dg = self._wg.get_design(graph_name)
        for old,new in replacements.items():
            if not isinstance(new,Node):
                new = Node(new[0],new[1],**new[2])
                replacements[old] = new

            old_gn = dg.nodes(old)            
            if (hasattr(new,"hasSequence") and 
                len(old_gn) > 0 and 
                hasattr(old_gn[0],"hasSequence")):
                n_s = new.hasSequence
                o_s = old_gn[0].hasSequence
                score = int(aligner.sequence_match(n_s,o_s)*100)
                if score > self._match_threshold and score != 100:
                    self._wg.truth.derivatives.positive(new,old_gn[0],score)
                else:
                    self._wg.truth.synonyms.positive(new,old)
            else:
                self._wg.truth.synonyms.positive(new,old)
            dg.replace_node(old,new.get_key(),new.properties)
        return replacements

    def _get_truth_absolute(self,entity,t_pes):
        res = self._wg.truth.node_query(entity)
        if len(res) != 0:
            assert(len(res) == 1)
            res = res[0]
            # 2. Entity is a synonym.
            if res.get_type() == nv_synonym:
                return self._resolve_synonym(res)
            # 1. Entity is directly in the network.
            return res,100
        if hasattr(entity,"hasSequence"):
            seq_props = {str(nv_has_sequence) : entity.hasSequence.upper()}
            res = self._wg.truth.node_query(**seq_props)
            if len(res) != 0:   
                # 3. Entity has a direct sequence match in the network.
                assert(len(res) == 1)
                return res[0],100


    def _get_external_absolute(self,entity,t_pes):
        name = entity.name
        record = self._miner.get(name)
        if record is not None:
            return self._miner.record_to_node(record,fragments=[name]),100
        if hasattr(entity,"hasSequence"):
            sequence = entity.hasSequence
            res = self._miner.sequence_match(sequence)
            if res is not None:
                record = self._miner.get(res[0])
                return self._miner.record_to_node(record,key=res),100
        return None


    def _get_truth_potential(self,entity,t_pes):
        potentials = {}
        qti = {"name" : self._get_name(entity.get_key())}
        results = self._wg.truth.query_text_index(qti,fuzzy=True)
        if len(results) > 0:
            # 4. Fuzzy String match & semantic type match
            for r,v in results.items():
                if self._are_related_type(r,entity):
                    potentials = self._add_potential(r,v,potentials)
                if r.get_type() == nv_synonym:
                    canonical,score = self._resolve_synonym(r)
                    if self._are_related_type(canonical,entity):
                        potentials = self._add_potential(canonical,
                                                        (score/100)*v,
                                                        potentials)

        if hasattr(entity,"hasSequence"):
            d_seq = entity.hasSequence.upper()
            d_seq_len = len(d_seq)
            highest_score = [None,0]
            for t_entity in t_pes:
                if hasattr(t_entity,"hasSequence"):
                    t_seq = t_entity.hasSequence.upper()
                    if aligner.string_length_diff(d_seq_len,len(t_seq)):
                        continue
                    score = int(aligner.sequence_match(d_seq,t_seq)*100)
                    if score > highest_score[1]:
                        highest_score = [t_entity,score]
            if highest_score[1] > self._match_threshold:
                # 5. Partial Sequence Match
                potentials = self._add_potential(*highest_score,
                                                  potentials)
        
        ds = [self._get_name(entity.get_key())]
        if hasattr(entity,"description"):
            ds += list(set(self._miner.prune_text(entity.description)))
        index = {nv_desc:ds}

        qti = self._wg.truth.query_text_index(index,fuzzy=True)
        qti.update(self._wg.truth.query_text_index(index)) 
        for k,v in qti.items():
            if not self._are_related_type(k,entity):
                continue
            if v <= 10:
                continue
            potentials = self._add_potential(k,v,potentials)
        return potentials


    def _get_external_potential(self,entity,t_pes):
        potentials = {}
        # 1. The entity description has a name of a external entity.
        if hasattr(entity,"description"):
            for d in list(set(self._miner.prune_text(entity.description))):
                for e in self._miner.get_entities(d):
                    record = self._get_record(e,entity)
                    if record is not None:
                        potentials = self._add_potential(record,50,
                                                         potentials)

        #2.  A external record has the name of the entity within 
        #    its descriptions.
        name = entity.name
        seens = []
        for db_result in self._miner.query(name):
            for result in db_result:
                if result in seens:
                    continue
                seens.append(result)
                record = self._get_record(result,entity)
                if record is None:
                    continue
                if record.get_key() in seens:
                    continue
                seens.append(record.get_key())
                potentials = self._add_potential(record,50,potentials)
        return potentials
    

    def _add_potential(self,entity,score,potentials):
        if entity in potentials:
            potentials[entity] = int(max([score,potentials[entity]]))
        else:
            potentials[entity] = int(score)
        return potentials
    

    def _get_record(self,name,existing_entity):
        record = self._miner.get(name)
        if record is not None:
            record = self._miner.record_to_node(record,fragments=[name])
            if record is None:
                return None
            if self._are_related_type(record,existing_entity):
                return record
        

    def _are_related_type(self,entity1,entity2):
        e1_t = entity1.get_type()
        e2_t = entity2.get_type()
        if  e1_t == e2_t:
            return True
        if model.is_derived(e1_t,e2_t):
            return True
        if model.is_derived(e2_t,e1_t):
            return True
        return False
    

    def _resolve_synonym(self,synonym):
        syn = self._wg.truth.synonyms.get(synonym=synonym)
        syn = list(syn.synonyms(synonym=synonym))
        return syn[0].n,syn[0].confidence
        
