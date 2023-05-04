import networkx as nx
from app.graph.utility.graph_objects.reserved_node import ReservedNode
from app.graph.utility.graph_objects.reserved_edge import ReservedEdge
from app.graph.utility.model.model import model

all_i_types = [str(i[1]["key"]) for i in model.get_derived(model.identifiers.objects.interaction)]
nv_derivative = str(model.identifiers.external.derivative)
class ViewGraph:
    def __init__(self, graph=None): 
        self._graph = graph if graph is not None else nx.MultiDiGraph()

    def resolve_node(func):
        def inner(self,n=None):
            if isinstance(n,ReservedNode):
                n = n.id
            return func(self,n)
        return inner
        
    def __len__(self):
        return len(self._graph)

    def __eq__(self, obj):
        if isinstance(obj, self.__class__):
            return nx.is_isomorphic(self._graph, obj._graph)
        if isinstance(obj, nx.MultiDiGraph):
            return nx.is_isomorphic(self._graph, obj)
        return False

    def __iter__(self):
        for n in self._graph.nodes:
            yield n

    def _node(self,labels,id=None,properties=None):
        if properties is None:
            props = {}
        else:
            props = properties
        return ReservedNode(labels,id=id,**props)
    
    def _edge(self,n,v,e,properties=None):
        if properties is None:
            props = {}
        else:
            props = properties
        return ReservedEdge(n,v,e,**props)

    def derivatives(self,node=None):
        for edge in self.out_edges(node):
            if edge.get_type() == nv_derivative:
                yield edge
        for edge in self.in_edges(node):
            if edge.get_type() == nv_derivative:
                yield ReservedEdge(edge.v,edge.n,edge.get_type(),
                                   **edge.get_properties())
                
    def interactions(self,interaction=None,entity=None,i_type=None):
        if i_type is None:
            i_type = all_i_types
        if not isinstance(i_type,list):
            i_type = [i_type]

        if entity is not None:
            for edge in self.in_edges(entity):
                if interaction is not None and edge.n.get_key() == interaction:
                    return edge.n
                if edge.n.get_type() in i_type:
                    yield edge.n
        else:
            for node in self.nodes():
                if interaction is not None and node.get_key() == interaction:
                    return node
                if node.get_type() in i_type:
                    yield node


    def interaction_elements(self,interaction):
        return self.out_edges(interaction)
    
    def nodes(self):
        for n,data in self._graph.nodes(data=True):
            props = data.copy()
            labels = props["key"]
            del props["key"]
            yield self._node(labels,id=n,properties=props)

    @resolve_node
    def edges(self,n=None):
        for n,v,e,d in self._graph.edges(n,keys=True,data=True):
            props = self._graph.nodes[n].copy()
            labels = props["key"]
            del props["key"]
            n = self._node(labels,id=n,properties=props)

            props = self._graph.nodes[v].copy()
            labels = props["key"]
            del props["key"]
            v = self._node(labels,id=v,properties=props)
            yield self._edge(n,v,e,properties=d)

    def get_node(self,n=None):
        if n is None:
            return list(self.nodes())
        data = self._graph.nodes[n]
        props = data.copy()
        labels = props["key"]
        del props["key"]
        return self._node(labels,id=n,properties=props)

    @resolve_node
    def in_edges(self, node=None):
        for n,v,e,d in self._graph.in_edges(node,keys=True,data=True):
            props = self._graph.nodes[n].copy()
            labels = props["key"]
            del props["key"]
            n = self._node(labels,id=n,properties=props)

            props = self._graph.nodes[v].copy()
            labels = props["key"]
            del props["key"]
            v = self._node(labels,id=v,properties=props)
            yield self._edge(n,v,e,properties=d)

    @resolve_node
    def out_edges(self, node=None):
        for n,v,e,d in self._graph.out_edges(node,keys=True,data=True):
            props = self._graph.nodes[n].copy()
            labels = props["key"]
            del props["key"]
            n = self._node(labels,id=n,properties=props)

            props = self._graph.nodes[v].copy()
            labels = props["key"]
            del props["key"]
            v = self._node(labels,id=v,properties=props)
            yield self._edge(n,v,e,properties=d)



    def has_edge(self,edge):
        return self._graph.has_edge(edge.n.id,edge.v.id,key=edge.get_type())
    
    def add_edge(self, edge):
        self._graph.add_edge(edge.n.id,edge.v.id,key=edge.get_type(),**edge.get_properties())

    def add_node(self, node):
        self._graph.add_node(node.id,key=node.get_key(),type=node.get_type(),**node.get_properties())

    def remove_edge(self, edge):
        self._graph.remove_edge(edge.n.id, edge.v.id, edge.get_type())

    def remove_node(self, node):
        self._graph.remove_node(node)
        
