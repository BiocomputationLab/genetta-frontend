from app.graph.utility.model.model import model
from app.graph.truth_graph.modules.abstract_module import AbstractModule
from app.graph.utility.graph_objects.reserved_node import ReservedNode
confidence = str(model.identifiers.external.confidence)

class InteractionModule(AbstractModule):
    def __init__(self,truth_graph):
        super().__init__(truth_graph)
    
    def get(self,subject=None,object=None,interaction=None,threshold=None):
        if threshold is None:
            threshold = self._default_threshold
        if interaction is None:
            interaction = [str(f[1]["key"]) for f in 
                           model.interaction_predicates()]
        if not isinstance(interaction,list):
            interaction = [interaction]
        res = []
        if object is not None:
            subject = [e.n for e in self._tg.edge_query(v=object,
                                                        e=interaction,
                                                        threshold=threshold)]
        else:
            subject = [subject]
        for s in subject:
            if s is not None and not isinstance(s,ReservedNode):
                s = ReservedNode(s,graph_name=self._tg.name)
            res += self._tg.edge_query(n=s,e=interaction)
        return self._to_graph(res)

    def positive(self,n,v,e,score=None):
        return super().positive(n,v,e,score)
            

    def negative(self,n,v,e,score=None):
        return super().positive(n,v,e,score)

