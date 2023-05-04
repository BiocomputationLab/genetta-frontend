from app.tools.visualiser.builder.builders.abstract_view import AbstractViewBuilder
from app.tools.visualiser.viewgraph.viewgraph import ViewGraph

class ProvenanceViewBuilder(AbstractViewBuilder):
    def __init__(self,graph):
        super().__init__(graph)

    def _subgraph(self, edges=[], nodes=[],new_graph=None):
        return ViewGraph(super()._subgraph(edges,nodes,new_graph))

    def build(self,predicate="ALL"):
        return self._subgraph(self._graph.derivatives.get())


