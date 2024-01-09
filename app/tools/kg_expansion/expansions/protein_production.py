from app.tools.kg_expansion.expansions.abstract_expansion import AbstractExpansion
from app.graph.utility.model.model import model
from app.graph.utility.graph_objects.reserved_edge import ReservedEdge

nv_p = str(model.identifiers.objects.protein)
nv_pp = str(model.identifiers.objects.genetic_production)
nv_template = str(model.identifiers.predicates.template)
nv_product = str(model.identifiers.predicates.product)
nv_activation = str(model.identifiers.objects.activation)
nv_repression = str(model.identifiers.objects.repression)
defered_int_types = [nv_activation,nv_repression]

class TruthProteinProduction(AbstractExpansion):
    '''
    It is assumed that all CDS express proteins.
    Also transfers any abstracted interactions 
    from the CDS to the new protein.
    '''
    def __init__(self, truth_graph, miner):
        super().__init__(truth_graph, miner)
    
    def expand(self):
        i_graph = self._tg.interactions.get()
        for cds in self._tg.get_cds():
            cds_ints = i_graph.interactions(participant=cds)
            pp_int = []
            defered_ints = []
            for i in cds_ints:
                if i.get_type() == nv_pp:
                    pp_int.append(i)
                elif i.get_type() in defered_int_types:
                    defered_ints.append(i)

            if len(pp_int) == 0:
                n = self._add_related_node(self._tg,cds,nv_pp)
                protein = self._add_related_node(self._tg,cds,nv_p)
                self._tg.interactions.positive(n,cds,nv_template,100)
                self._tg.interactions.positive(n,protein,nv_product,100)
            elif len(defered_ints) > 0:
                assert(len(pp_int) == 1)
                protein = [p for p in i_graph.interactions(pp_int[0]) if 
                           p.v.get_type() == nv_p]
                assert(len(protein) == 1)
                protein = protein[0].v

            for di in defered_ints:
                for inter in i_graph.interactions(interaction=di):
                    if inter.v == cds:
                        self._tg.remove_edges([inter])
                        inter.v = protein
                        self._tg.add_edges([inter],modifier=inter.confidence)




