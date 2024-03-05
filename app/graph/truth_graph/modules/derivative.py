from app.graph.utility.graph_objects.reserved_edge import ReservedEdge
from app.graph.utility.model.model import model
from app.graph.truth_graph.modules.abstract_module import AbstractModule

confidence = str(model.identifiers.external.confidence)
p_derivative = str(model.identifiers.external.derivative)
dpn = "TruthDerivativeProject"
class DerivativeModule(AbstractModule):
    def __init__(self,truth_graph):
        super().__init__(truth_graph)
    
    def get(self,subject=None,derivative=None,threshold=None,directed=False):
        if threshold is None:
            threshold = self._default_threshold
        if subject is None and derivative is None:
            directed = True
        e = ReservedEdge(n=subject,v=derivative,type=p_derivative,
                         graph_name=self._tg.name)
        res = self._tg.edge_query(e=e,directed=directed,
                                  threshold=threshold)
        return self._to_graph(res)

    def _check_projection(self):
        try:
            g_count = self._tg.project.get_graph(dpn).relationship_count()
            if (g_count != self._tg.count_edges(p_derivative)):
                self._tg.project.drop(dpn)
                self._tg.project.derivative(dpn)
        except ValueError:
            self._tg.project.derivative(dpn)


    def positive(self,subject,derivative,score=None):
        subject = self._cast_node(subject)
        derivative = self._cast_node(derivative)
        # Check if the subject is in the graph.
        if score is None:
            score = self._standard_modifier
        if score < 1:
            score = int(score *100)
        res = self._tg.edge_query(n=subject,v=derivative,e=p_derivative)
        if len(res) != 0:
            assert(len(res) == 1)
            return self._update_confidence(res[0],score)
        res = self._tg.edge_query(n=derivative,v=subject,e=p_derivative)
        if len(res) != 0:
            assert(len(res) == 1)
            return self._update_confidence(res[0],score)
        edge = self._cast_edge(subject,derivative,p_derivative,name="Derivative")
        return self._add_new_edge(edge,score)



    def negative(self,subject,derivative,score=None):
        subject = self._cast_node(subject)
        derivative = self._cast_node(derivative)
        # Check if the subject is in the graph.
        if score is None:
            score = self._standard_modifier
        if score < 1:
            score = int(score *100)
        res = self._tg.edge_query(n=subject,v=derivative,e=p_derivative)
        if len(res) != 0:
            assert(len(res) == 1)
            return self._update_confidence(res[0],-score)
        res = self._tg.edge_query(n=derivative,v=subject,e=p_derivative)
        if len(res) != 0:
            assert(len(res) == 1)
            return self._update_confidence(res[0],-score)


    def get_components(self):
        der_graph = self.get()
        components = der_graph.weakly_connected_components()
        component_graphs = []
        for component in components:
            edges = []
            for e in component:
                res = der_graph.get_node(e)
                edges += set(list(der_graph.edges(res)))
            component_graphs.append(self._to_graph(edges))
        return component_graphs
        
        
    def are_derivatives(self,entity1,entities):
        d_graph = self.get()
        if not d_graph.has_node(entity1):
            return False
        entities = [e for e in entities if d_graph.has_node(e)]
        if len(entities) == 0:
            return False
        res = self._tg.procedure.dijkstra_sp(dpn,
                                             entity1,entities)
        if len(res) == 0:
            return False
        return True