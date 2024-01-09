from app.graph.utility.model.model import model
from app.graph.truth_graph.modules.abstract_module import AbstractModule
from app.graph.utility.graph_objects.node import Node

confidence = str(model.identifiers.external.confidence)
nv_module = model.identifiers.objects.module
nv_module_cc = model.get_class_code(nv_module)
nv_has_interaction = str(model.identifiers.predicates.hasInteraction)
nv_mod_preds = [str(s) for s in model.get_predicates(nv_module_cc)]

class InteractionModuleModule(AbstractModule):
    def __init__(self,truth_graph):
        super().__init__(truth_graph)
    
    def get(self,module=None,object=None,predicate=None,threshold=None):
        if threshold is None:
            threshold = self._default_threshold
        if predicate is None:
            predicate = nv_mod_preds
        res = []
        if module is not None:
            module = self._cast_node(module)
            res += self._tg.edge_query(n=module,e=predicate)
        elif object is not None:
            object = self._cast_node(object)
            res += self._tg.edge_query(v=object,e=predicate)
        else:
            res += self._tg.edge_query(e=predicate)
        return self._to_graph(res)


    def positive(self,n,v,e,score=None):
        if not isinstance(n,Node):
            n = Node(n,nv_module)
        return super().positive(n,v,e,score)
            
    def negative(self,n,v,e,score=None):
        return super().positive(n,v,e,score)

