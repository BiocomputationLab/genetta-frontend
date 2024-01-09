import re
from abc import ABC
from app.graph.utility.model.model import model
from app.graph.utility.graph_objects.reserved_edge import ReservedEdge
from app.graph.utility.graph_objects.reserved_node import ReservedNode
from app.graph.utility.graph_objects.node import Node
from app.graph.truth_graph.modules.viewgraph import ViewGraph
import networkx as nx
confidence = str(model.identifiers.external.confidence)
p_synonym = str(model.identifiers.external.synonym)

class AbstractModule(ABC):
    def __init__(self,truth_graph):
        self._tg = truth_graph
        self._standard_modifier = 5
        self._upper_threshold = 100
        self._lower_threshold = 0
        self._default_threshold=80
    

    def _to_graph(self,edges):
        g = ViewGraph()
        for edge in edges:
            edge = self._cast_condfidence([edge])[0]
            g.add_node(edge.n)
            g.add_node(edge.v)
            g.add_edge(edge)
        return g
    
    def positive(self,n,v,e,score=None):
        n = self._cast_node(n)
        v = self._cast_node(v)
        if score is None:
            score = self._standard_modifier
        if score < 1:
            score = int(score *100)
        edge = self._cast_edge(n,v,e)
        # Check if the subject is in the graph.
        res = self._tg.edge_query(n=edge.n,v=edge.v,e=edge.get_type())
        if len(res) != 0:
            assert(len(res) == 1)
            return self._update_confidence(res[0],score)
        else:
            return self._add_new_edge(edge,score)
    
    def negative(self,n,v,e,score=None):
        n = self._cast_node(n)
        v = self._cast_node(v)
        if score is None:
            score = self._standard_modifier
        if score < 1:
            score = int(score *100)
        edge = self._cast_edge(n,v,e)
        # Check if the subject is in the graph.
        res = self._tg.edge_query(n=edge.n,v=edge.v,e=edge.get_type())
        if len(res) != 0:
            assert(len(res) == 1)
            return self._update_confidence(res[0],-score)

    def get(self,edge):
        res = self._tg.edge_query(e=edge)
        if len(res) == 0:
            return None
        res = self._cast_condfidence(res)
        assert(len(res) == 1)
        return res[0]

    
    def upper_threshold(self):
        pass
    
    def _cast_edge(self,n,v,e,**kwargs):
        n = self._cast_node(n)
        v = self._cast_node(v)
        edge = ReservedEdge(n,v,e,graph_name=self._tg.name,**kwargs)
        return edge
        
    def _cast_node(self,subject,n_type=None,props=None):
        if props is None:
            props = {}
        if not isinstance(subject,ReservedNode):
            if isinstance(subject,Node):
                n_type = subject.get_type()
                props = subject.properties
                subject = subject.get_key()
                if "graph_name" in props:
                    del props["graph_name"]
            subject = ReservedNode(subject,n_type,
                                   graph_name=self._tg.name,**props)
        subject.properties["graph_name"] = self._tg.name
        subject.graph_name = self._tg.name
        return subject

    def _change(self,edges,modifier):
        if not isinstance(edges,(list,set,tuple)):
            edges = [edges]
        for edge in edges:
            if not isinstance(edge,ReservedEdge):
                raise ValueError(f'{edge} must be an edge.')
            eq = self._tg.edge_query(e=edge)
            if eq != []:
                eq = self._cast_condfidence(eq)
                assert(len(eq) == 1)
                eq = eq[0]
                self._update_confidence(eq,modifier)
                continue
            # Don't add feedback with no confidence.
            if modifier > 0:
                self._add_new_edge(edge)

    def _add_new_edge(self,edge,confidence=None):
        nq = self._tg.node_query([edge.n,edge.v])
        if nq != []:
            assert(edge.n in nq or edge.v in nq)
            if edge.n not in nq:
                self._tg.add_node(edge.n)
            if edge.v not in nq:
                self._tg.add_node(edge.n)
        if confidence is None:
            confidence = self._standard_modifier
        self._tg.add_edges(edge,confidence)

    def _update_confidence(self,edge,modifier):
        conf = edge.get_properties()[confidence]
        new_conf = int(conf) + modifier
        if new_conf >= self._upper_threshold:
            self._tg.set_confidence(edge,100)
            self._upper_change(edge)
        elif new_conf <= self._lower_threshold:
            self._lower_change(edge)
        else:
            self._tg.set_confidence(edge,new_conf)

    def _upper_change(self,edge):
        pass

    def _lower_change(self,edge):
        nedges = self._tg.edge_query(n=edge.n,directed=False)
        vedges = self._tg.edge_query(n=edge.v,directed=False)
        if len(nedges) == 1:
            self._tg.remove_node(edge.n)
        if len(vedges) == 1:
            self._tg.remove_node(edge.v)
        self._tg.remove_edges(edge)

    def _cast_condfidence(self,res):
        for r in res:
            c_val = int(r[confidence])
            r.set_confidence(c_val)
        return res