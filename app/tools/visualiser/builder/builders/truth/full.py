from app.tools.visualiser.builder.builders.abstract_view import AbstractViewBuilder
from app.tools.visualiser.viewgraph.viewgraph import ViewGraph
from  app.graph.utility.model.model import model
bl_preds = [str(model.identifiers.external.synonym)]
class TruthFullViewBuilder(AbstractViewBuilder):
    def __init__(self,graph):
        super().__init__(graph)

    def _subgraph(self, edges=[], nodes=[],new_graph=None):
        return ViewGraph(super()._subgraph(edges,nodes,new_graph))
        
    def build(self,predicate="ALL"):
        edges = [e for e in self._graph.edges(predicate=predicate) 
                 if e.get_type() not in bl_preds]
        return self._subgraph(edges)