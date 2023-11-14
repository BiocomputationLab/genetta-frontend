from app.tools.visualiser.builder.design import DesignBuilder
from app.tools.visualiser.builder.builders.truth.provenance import ProvenanceViewBuilder
from app.tools.visualiser.builder.builders.truth.synonym import SynonymViewBuilder
from app.tools.visualiser.builder.builders.truth.module import ModuleViewBuilder
class TruthBuilder(DesignBuilder):
    def __init__(self, graph):
        super().__init__(graph)
        self._dg = graph.truth

    def set_module_view(self):
        self._view_builder = ModuleViewBuilder(self._dg)

    def set_provenance_view(self):
        self._view_builder = ProvenanceViewBuilder(self._dg)

    def set_synonym_view(self):
        self._view_builder = SynonymViewBuilder(self._dg)

    def v_nodes(self):
        return self.view.nodes(reserved=True)

    def v_edges(self,n=None):
        return self.view.edges(n,reserved=True)

    def in_edges(self, n=None):
        return self.view.in_edges(n,reserved=True)

    def out_edges(self, n=None):
        return self.view.out_edges(n,reserved=True)
            
    def get_root_entities(self):
        return self._dg.get_root_entities()