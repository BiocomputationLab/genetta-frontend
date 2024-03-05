from app.graph.design_graph.gds.project import ProjectBuilder
class TruthProjectBuilder(ProjectBuilder):
    def __init__(self, graph):
        super().__init__(graph)
    
    def derivative(self,name):
        edge_labels = [self._ids.external.derivative]
        node_props = {"graph_name" : self._graph.name}
        res = self._driver.project.cypher_project(name,
                                                  edge_labels=edge_labels,
                                                  node_properties=node_props)
        return res