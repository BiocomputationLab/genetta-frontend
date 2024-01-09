from app.graph.design_graph.gds.project import ProjectBuilder
class TruthProjectBuilder(ProjectBuilder):
    def __init__(self, graph):
        super().__init__(graph)
    
    def derivative(self,name,derivatives=None,direction="UNDIRECTED"):
        e = {self._ids.external.derivative:{"orientation" : direction}}
        n = []
        if derivatives is None:
            derivatives = self._graph.derivatives.get()
        for edge in derivatives.derivatives():
            n += [str(edge.n),str(edge.v)]
        n = self._cast(list(set(n)))
        return self._driver.project.project(name,n,e)[0]