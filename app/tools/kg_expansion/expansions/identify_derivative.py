from app.tools.kg_expansion.expansions.abstract_expansion import AbstractExpansion
from app.graph.utility.model.model import model
from app.tools.aligner import aligner
nv_dna = str(model.identifiers.objects.dna)
nv_dna_cc = model.get_class_code(nv_dna)

class TruthDerivative(AbstractExpansion):
    def __init__(self, truth_graph, miner):
        super().__init__(truth_graph, miner)
    
    def expand(self):
        '''
        Identifies potential sequence based connections 
        such as derived or identical types within the physcial entities.
        '''
        res = {}
        d_graph = self._tg.derivatives.get()
        wcc = list(d_graph.weakly_connected_components())

        for p in self._tg.get_physicalentity():
            if not hasattr(p,"hasSequence"):
                continue
            sequence = p.hasSequence.strip().upper()
            if sequence in res:
                entity = res[sequence]
                self._tg.merge_nodes(entity,p)
                self._tg.synonyms.positive(entity,p.get_key(),
                                           score=100)
            else:
                res[sequence] = p
        
        for seq, entity in res.items():
            seq_len = len(seq)
            highest_score = [0,None]
            cands = self._candidates(seq,res,entity.id,wcc)
            while len(cands) > 0:
                s1,e1 = cands.pop()
                if seq == s1:
                    continue
                if aligner.string_length_diff(seq_len,len(s1)):
                    continue
                score = int(aligner.sequence_match(s1,seq)*100)
                if score > highest_score[0]:
                    highest_score = [score,e1]
            if highest_score[0] > self._match_threshold:
                self._tg.derivatives.positive(highest_score[1],entity,
                                              highest_score[0])
                wcc = self._merge_wcc(wcc,highest_score[1],entity)

    def _merge_wcc(self,wcc,entity1,entity2):
        i1 = None
        i2 = None
        for index,wc in enumerate(wcc):
            if entity1.id in wc:
                i1 = index
            if entity2.id in wc:
                i2 = index
            if i1 is not None and i2 is not None:
                break

        if i1 is None:
            i1w = {entity1.id}
        else:
            i1w = wcc.pop(i1)
        if i2 is None:
            i2w = {entity2.id}
        else:
            if i1 is not None and i2 > i1:
                i2 -= 1
            i2w = wcc.pop(i2)
        
        i1w.update(i2w)
        wcc += [i1w]
        return wcc
                
    def _candidates(self,sequence,e_dict,e_id,derivatives):    
        dna_bases = set("ACGT") 
        rna_bases = set("ACGU")
        aa_bases = set("ACDEFGHIKLMNPQRSTVWY")
        derivatives = [d for d in derivatives if e_id in d]
        assert(len(derivatives) <= 1)
        if len(derivatives) == 1:
            derivatives = derivatives[0]
        def is_dna(seq):
            return set(seq).issubset(dna_bases)
        def is_rna(seq):
            return set(seq).issubset(rna_bases)
        def is_protein(seq):
            return set(seq).issubset(aa_bases)
        
        if is_dna(sequence):
            return [(k,v) for k,v in e_dict.items() if is_dna(sequence) 
                    and v.id not in derivatives]
        if is_rna(sequence):
            return [(k,v) for k,v in e_dict.items() if is_rna(sequence) 
                    and v.id not in derivatives]
        if is_protein(sequence):
            return [(k,v) for k,v in e_dict.items() if is_protein(sequence) 
                    and v.id not in derivatives]