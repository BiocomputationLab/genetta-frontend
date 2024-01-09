from app.graph.utility.graph_objects.reserved_edge import ReservedEdge
from app.graph.utility.model.model import model
from app.graph.truth_graph.modules.abstract_module import AbstractModule
p_cuw = str(model.identifiers.predicates.commonly_used_with)
class UsageModule(AbstractModule):
    def __init__(self,truth_graph):
        super().__init__(truth_graph)
    
    def get(self,subject=None,object=None,threshold=None):
        if threshold is None:
            threshold = self._default_threshold
        e = ReservedEdge(n=subject,v=object,type=p_cuw,
                         graph_name=self._tg.name)
        res = self._tg.edge_query(e=e,threshold=threshold)
        return self._to_graph(res)
    

    def positive(self,subject,object,score=None):
        subject = self._cast_node(subject)
        object = self._cast_node(object)
        # Check if the subject is in the graph.
        if score is None:
            score = self._standard_modifier
        if score < 1:
            score = int(score *100)
        res = self._tg.edge_query(n=subject,v=object,e=p_cuw)
        if len(res) != 0:
            assert(len(res) == 1)
            return self._update_confidence(res[0],score)
        res = self._tg.edge_query(n=object,v=subject,e=p_cuw)
        if len(res) != 0:
            assert(len(res) == 1)
            return self._update_confidence(res[0],score)
        edge = self._cast_edge(subject,object,p_cuw)
        return self._add_new_edge(edge,score)



    def negative(self,subject,object,score=None):
        subject = self._cast_node(subject)
        object = self._cast_node(object)
        # Check if the subject is in the graph.
        if score is None:
            score = self._standard_modifier
        if score < 1:
            score = int(score *100)
        res = self._tg.edge_query(n=subject,v=object,e=p_cuw)
        if len(res) != 0:
            assert(len(res) == 1)
            return self._update_confidence(res[0],-score)
        res = self._tg.edge_query(n=object,v=subject,e=p_cuw)
        if len(res) != 0:
            assert(len(res) == 1)
            return self._update_confidence(res[0],-score)