from Bio.Seq import Seq
from app.tools.graph_query.datatype_handlers.abstract_handler import AbstractHandler
from app.graph.utility.model.model import model
from app.tools.aligner import aligner

p_has_sequence = str(model.identifiers.predicates.has_sequence)
class SequenceHandler(AbstractHandler):
    def __init__(self,graph):
        super().__init__(graph)
        self._threshold = 80
        self._min_threshold = 40

    def get_name(self):
        return "Sequence"
    
    def get_description(self):
        return "Returns genetic parts based on sequence matching."
    
    def get_example(self):
        return "tttaattatatatatatatatatataatggaagcgtttt"
    
    def handle(self,query,strict=False):
        results = {}
        e_res = []
        sequence = query.strip().upper()
        f_match = self._graph.node_query(**{p_has_sequence:sequence})
        if len(f_match) != 0:
            assert(len(f_match) == 1)
            e_res.append(self._add_match(100,f_match[0]))
            d_graph = self._graph.derivatives.get(f_match[0])
            for derivative in d_graph.derivatives():
                if derivative.confidence > self._threshold:
                    e_res.append(self._add_match(derivative.confidence,
                                                 derivative.v))
            e_res = self._rank_result(e_res)
            return {f_match[0].get_key(): e_res}
        elif not strict:
            seq_len = len(sequence)
            d_graph = self._graph.derivatives.get()
            candidates = self._get_sequence_type(sequence)
            while len(candidates) > 0:
                candidate = candidates.pop()
                c_seq = candidate.hasSequence
                if aligner.string_length_diff(seq_len,len(c_seq)):
                    continue
                score = int(aligner.sequence_match(c_seq,sequence)*100)
                if score > self._threshold:
                    e_res.append(self._add_match(score,candidate))
                elif score < self._min_threshold:
                    candidates = self._prune_derivatives(candidate,
                                                         candidates,
                                                         d_graph)
        if len(e_res) > 0:
            e_res = self._rank_result(e_res)
            results[None] = e_res
        return results
    
    def feedback(self, source, result, positive=True):
        '''
        It is not clear what feedback would mean here.
        Source = Entity | None | 
        Result = Entity
        '''
        if source == result:
            return
        if source is None:
            return
        if positive:
            self._graph.derivatives.positive(source,result)
        else:
            self._graph.derivatives.negative(source,result)
                
    def _prune_derivatives(self,candidate,candidates,d_graph):
        '''
        Removes all derivatives of low score candidate.
        '''
        derivs = [d.v for d in d_graph.derivatives(candidate)]
        return list(set(candidates) - set(derivs))

    def _get_sequence_type(self,sequence):
        sequence = Seq(sequence)        
        dna_bases = set("ACGT")
        if set(sequence).issubset(dna_bases):
            return  self._graph.get_dna()
        rna_bases = set("ACGU")
        if set(sequence).issubset(rna_bases):
            return self._graph.get_rna()
        aa_bases = set("ACDEFGHIKLMNPQRSTVWY")
        if set(sequence).issubset(aa_bases):
            return self._graph.get_protein()
        return []

    def _add_match(self,conf,entity):
        return (conf,{"description" : self._get_name(entity.get_key()), 
                      "entity" : entity.get_key()})
    
