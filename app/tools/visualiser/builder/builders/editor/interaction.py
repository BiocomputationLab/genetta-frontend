from app.tools.visualiser.builder.builders.design.interaction import InteractionViewBuilder
from app.tools.visualiser.builder.builders.design.utility import produce_interaction_graph
from app.graph.utility.model.model import model
from app.graph.utility.graph_objects.node import Node
from app.tools.visualiser.builder.builders.editor.common_builds import build_interaction_uri
from app.tools.visualiser.builder.builders.editor.common_builds import create_consists_of
from app.tools.visualiser.builder.builders.editor.common_builds import build_properties

class EditorInteractionViewBuilder(InteractionViewBuilder):
    def __init__(self,graph):
        super().__init__(graph)

    def build(self,predicate="ALL"):
        g = produce_interaction_graph(self._graph)
        g = self._subgraph(new_graph=g)
        for node in self._graph.get_physicalentity(predicate=predicate):
            g.add_node(node)
        return g

    def get_edge_types(self):
        c_id = model.get_class_code(model.identifiers.objects.interaction)
        return [k[1]["key"] for k in model.get_derived(c_id)]
    
    def get_node_types(self):
        c_id = model.get_class_code(model.identifiers.objects.physical_entity)
        return [k[1]["key"] for k in model.get_derived(c_id)]

    def transform(self,n,v,e):
        et = [str(n) for n in self.get_edge_types()]
        nt = [str(n) for n in self.get_node_types()]
        n = {str(nn) : nv for nn,nv in n.items()}
        v = {str(vn) : vv for vn,vv in v.items()}
        edges = []
        if e not in et:
            return []
        
        # Checking for an conceptual match for an existing interaction.
        for edge in self._graph.get_interactions(list(n.values())[0]):
            if edge.n.get_type() == e:
                i_eles = self._graph.get_interaction_elements(edge.n)
                i_parts = {e.get_type():e.v for e in i_eles}
                all_eles = n 
                all_eles.update(v)
                if i_parts == all_eles:
                    edges += [(e.n,e.v,e.get_type(),e.properties) 
                              for e in i_eles]
                    edges += [(e.n,e.v,e.get_type(),e.properties) for
                               e in self._graph.get_consists_of(edge.n)]
                return edges
            
        node_uri = build_interaction_uri(n,v,e)
        i_node = Node(node_uri,e,**build_properties(node_uri,self._graph.name))

        model_code = model.get_class_code(e)
        inputs,outputs = model.interaction_predicates(model_code)
        inputs = [str(i[1]["key"]) for i in inputs]
        outputs = [str(o[1]["key"]) for o in outputs]
        
        for pred,node in n.items():
            pred = str(pred)
            if pred not in inputs:
                continue
            if node.get_type() not in nt:
                continue
            edges.append((i_node,node,pred,build_properties(pred,self._graph.name)))
        for pred,node in v.items():
            pred = str(pred)
            if pred not in outputs:
                continue
            if node.get_type() not in nt:
                continue
            edges.append((i_node,node,pred,build_properties(pred,self._graph.name)))
        if len(edges) > 0:
            edges += create_consists_of(i_node,self._graph.name)
        return edges