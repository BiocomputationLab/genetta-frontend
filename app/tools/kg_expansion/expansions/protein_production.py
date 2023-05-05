from app.tools.kg_expansion.expansions.abstract_expansion import AbstractExpansion
from app.graph.utility.model.model import model

nv_i = model.identifiers.objects.input
nv_o = model.identifiers.objects.output
nv_p = model.identifiers.objects.protein
nv_pp = model.identifiers.objects.genetic_production
nv_template = model.identifiers.predicates.template
nv_product = model.identifiers.predicates.product

class TruthProteinProduction(AbstractExpansion):
    '''
    It is assumed that all CDS express proteins.
    '''
    def __init__(self, truth_graph, miner):
        super().__init__(truth_graph, miner)
    
    def enhance(self):
        i_graph = self._tg.interactions.get()
        for cds in self._tg.get_cds():
            for i in i_graph.interactions(entity=cds):
                if i.n.get_type() == str(nv_pp):
                    break
            else:
                n = self._add_related_node(self._tg,cds,nv_pp)
                v = self._add_related_node(self._tg,cds,nv_p)
                self._tg.interactions.positive(n,cds,nv_template,100)
                self._tg.interactions.positive(n,v,nv_product,100)



