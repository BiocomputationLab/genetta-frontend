from rdflib import RDF
from app.tools.visualiser.builder.builders.abstract_view import AbstractViewBuilder
from  app.graph.utility.model.model import model
from app.tools.visualiser.viewgraph.viewgraph import ViewGraph
from app.graph.utility.graph_objects.edge import Edge

bl_pred = {str(model.identifiers.predicates.consistsOf),str(RDF.type)}
w_predicates = list({str(p) for p in model.identifiers.predicates} - bl_pred)
                    

class PositionViewBuilder(AbstractViewBuilder):
    def __init__(self,graph):
        super().__init__(graph)

    def _subgraph(self, edges=[],nodes=[], new_graph=None):
        return ViewGraph(super()._subgraph(edges,nodes,new_graph))

    def build(self,predicate="ALL"):
        edges = []
        for position in self._graph.get_position(predicate=predicate):
            posof = self._graph.get_positionof(position,predicate="ANY")
            assert(len(posof) == 1)
            posof = posof[0].v
            nex = self._graph.get_next(position)
            if len(nex) == 0:
                continue
            assert(len(nex) == 1)
            nex = nex[0]
            v = self._graph.get_positionof(nex.v,predicate="ANY")
            assert(len(v) == 1)
            v = v[0].v
            edges.append(Edge(posof, v, nex.get_type(),**nex.properties))

        return self._subgraph(edges)

