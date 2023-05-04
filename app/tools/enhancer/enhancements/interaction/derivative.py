from app.tools.enhancer.enhancements.abstract_enhancements import AbstractEnhancement
from app.graph.utility.model.model import model

nv_dna = str(model.identifiers.objects.dna)
nv_dna_cc = model.get_class_code(nv_dna)


class TruthDerivative(AbstractEnhancement):
    def __init__(self, world_graph, miner):
        super().__init__(world_graph, miner)

    def enhance(self):
        '''
        For each existing interaction find any derivatives of participants.
        If the derivatives dont encode this interaction, then add another.
        The confidence is based on the derivative confidence.
        '''
        graph = self._wg.truth
        i_graph = graph.interactions.get()
        d_graph = graph.derivatives.get()
        for derivative in d_graph.derivatives():
            for interaction in i_graph.interactions(entity=derivative.n):
                considered = [derivative.n]
                ie = list(i_graph.interaction_elements(interaction))
                d_derivatives = [derivative]
                while len(d_derivatives) > 0:
                    d_derivative = d_derivatives.pop()
                    if d_derivative.v in considered:
                        continue
                    considered.append(d_derivative.v)
                    for d_i in i_graph.interactions(entity=d_derivative.v):
                        d_i_eles = list(i_graph.interaction_elements(d_i))
                        if d_i.get_type() != interaction.get_type():
                            continue
                        d_i_eles_ve = [(d.v, d.get_type()) for d in d_i_eles if d.v != d_derivative.v]
                        ie_ve = [(d.v, d.get_type()) for d in ie if d.v != derivative.n]        
                        if len(list(set(d_i_eles_ve) ^ set(ie_ve))) != 0:
                            continue
                        break
                    else:
                        dup_i = self._add_related_node(graph, d_derivative.v, interaction.get_type())
                        for ele in ie:
                            if ele.v == derivative.n:
                                obj = d_derivative.v
                            else:
                                obj = ele.v
                            graph.interactions.positive(dup_i, obj, ele.get_type(), d_derivative.confidence)
                    d_derivatives += list(d_graph.derivatives(d_derivative.v))


    def apply(self, cds):
        pass
