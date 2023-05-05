from app.tools.kg_expansion.expansions.abstract_expansion import AbstractExpansion
from app.graph.utility.model.model import model

nv_dna = str(model.identifiers.objects.dna)
nv_dna_cc = model.get_class_code(nv_dna)


class TruthDerivative(AbstractExpansion):
    def __init__(self, truth_graph, miner):
        super().__init__(truth_graph, miner)

    def expand(self):
        '''
        For each existing interaction find any derivatives of participants.
        If the derivatives dont encode this interaction, then add another.
        The confidence is based on the derivative confidence.
        '''
        i_graph = self._tg.interactions.get()
        d_graph = self._tg.derivatives.get()
        for der in d_graph.derivatives():
            for i in i_graph.interactions(entity=der.n):
                considered = [der.n]
                ie = list(i_graph.interaction_elements(i))
                d_ders = [der]
                while len(d_ders) > 0:
                    d_der = d_ders.pop()
                    if d_der.v in considered:
                        continue
                    considered.append(d_der.v)
                    for d_i in i_graph.interactions(entity=d_der.v):
                        d_i_eles = list(i_graph.interaction_elements(d_i))
                        if d_i.get_type() != i.get_type():
                            continue
                        d_i_eles_ve = [(d.v, d.get_type())
                                       for d in d_i_eles if d.v != d_der.v]
                        ie_ve = [(d.v, d.get_type())
                                 for d in ie if d.v != der.n]
                        if len(list(set(d_i_eles_ve) ^ set(ie_ve))) != 0:
                            continue
                        break
                    else:
                        dup_i = self._add_related_node(
                            self._tg, d_der.v, i.get_type())
                        for ele in ie:
                            if ele.v == der.n:
                                obj = d_der.v
                            else:
                                obj = ele.v
                            self._tg.interactions.positive(
                                dup_i, obj, ele.get_type(), d_der.confidence)
                    d_ders += list(d_graph.derivatives(d_der.v))
