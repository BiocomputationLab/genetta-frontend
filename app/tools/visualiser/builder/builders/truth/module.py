from app.tools.visualiser.builder.builders.abstract_view import AbstractViewBuilder
from app.tools.visualiser.viewgraph.viewgraph import ViewGraph
from app.graph.utility.graph_objects.edge import Edge
class ModuleViewBuilder(AbstractViewBuilder):
    def __init__(self,graph):
        super().__init__(graph)

    def _subgraph(self, edges=[], nodes=[],new_graph=None):
        return ViewGraph(super()._subgraph(edges,nodes,new_graph))

    def build(self,predicate="ALL"):
        module_graph = self._graph.modules.get()
        edges = []
        for module in module_graph.modules():
            for interaction in module_graph.modules(module):
                interaction = interaction.v.duplicate()
                interaction.id = f'{interaction.get_key()}_{module}'
                inputs, outputs = self._graph.get_interaction_io(interaction,predicate=predicate)
                for obj in inputs:
                    n = obj.v.duplicate()
                    n.id = f'{n.get_key()}_{module}'
                    edges.append((Edge(n, interaction, obj.get_type(), **obj.get_properties())))
                for obj in outputs:
                    v = obj.v.duplicate()
                    v.id = f'{v.get_key()}_{module}'
                    edges.append((Edge(interaction,v, obj.get_type(), **obj.get_properties())))
        return self._subgraph(edges)


