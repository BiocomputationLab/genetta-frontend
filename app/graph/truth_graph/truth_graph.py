import json

from app.graph.utility.model.model import model
from app.graph.design_graph.design_graph import DesignGraph
from app.graph.truth_graph.modules.synonym import SynonymModule
from app.graph.truth_graph.modules.derivative import DerivativeModule
from app.graph.truth_graph.modules.interaction import InteractionModule
from app.graph.truth_graph.modules.module import InteractionModuleModule
from app.graph.truth_graph.modules.usage import UsageModule
from app.graph.utility.graph_objects.edge import Edge
from app.graph.utility.graph_objects.reserved_edge import ReservedEdge
from app.graph.utility.graph_objects.reserved_node import ReservedNode
from app.graph.truth_graph.gds.procedures import TruthProcedures
from app.graph.truth_graph.gds.project import TruthProjectBuilder

p_confidence = str(model.identifiers.external.confidence)
p_synonym = str(model.identifiers.external.synonym)
o_pe = model.identifiers.objects.physical_entity
index_name = "truth_index"
index_labels = ([model.identifiers.objects.synonym] + 
                [str(k[1]["key"]) for k in model.get_derived(o_pe)])
index_on = ["name",model.identifiers.external.description] 

class TruthGraph(DesignGraph):
    def __init__(self, name, driver):
        super().__init__(driver,name)
        self.procedure = TruthProcedures(self)
        self.project = TruthProjectBuilder(self)
        self.synonyms = SynonymModule(self)
        self.interactions = InteractionModule(self)
        self.derivatives = DerivativeModule(self)
        self.modules = InteractionModuleModule(self)
        self.usage = UsageModule(self)
        self._np = {"graph_name": self.name}
        self._create_text_index(index_name,index_labels,index_on)
    

    def add_node(self,key,type=None,**kwargs):
        kwargs.update(self._np)
        if "sequence" in kwargs:
            kwargs = self._format_sequence(kwargs["sequence"],kwargs)
        if "description" in kwargs:
            kwargs = self._format_description(kwargs["description"],kwargs)
        kwargs = self._format_name(key,kwargs)
        n = self.driver.add_node(key,type,**kwargs)
        self.driver.submit(log=False)
        return n
    
    def add_edges(self, edges, modifier=5):
        if not isinstance(edges,list):
            edges = [edges]
        if modifier <= 0:
            return
        for e in edges:
            n,v,e,props = self._derive_edge_elements(e)
            props[p_confidence] = modifier
            n,v,props = self._add_graph_names_edge(n,v,props)
            self.driver.add_edge(n,v,e,**props)
        self.driver.submit(log=False)

    def remove_edges(self,edges):
        if not isinstance(edges,list):
            edges = [edges]
        for e in edges:
            n,v,e,props = self._derive_edge_elements(e)
            n,v,props = self._add_graph_names_edge(n,v,props)
            self.driver.remove_edge(n,v,e,**props)
        self.driver.submit(log=False)

    def set_confidence(self, edge, confidence):
        self.driver.set_edge(edge, {p_confidence: confidence})
        return self.driver.submit(log=False)

    def merge_nodes(self,source,merged):
        properties = {model.identifiers.external.description:"'combine'"}
        self.driver.merge_nodes(source,merged,properties=properties)
        return self.driver.submit(log=False)

    def node_query(self, n=[], **kwargs):
        return self._node_query(n,**kwargs)

    def edge_query(self, n=None, v=None, e=None, threshold=0, **kwargs):
        n = self._add_node_gn(n)
        v = self._add_node_gn(v)
        return [e for e in self._edge_query(n,e,v,**kwargs) 
                if int(e[p_confidence]) >= threshold]

    def query_text_index(self,values,predicate=None,wildcard=False,
                         fuzzy=False,threshold=None):
        if predicate is None:
            predicate = "OR"
        return self.driver.query_text_index(index_name,values,
                                            graph_names=self.name,
                                            predicate=predicate,
                                            wildcard=wildcard,
                                            fuzzy=fuzzy,
                                            threshold=threshold)
    
    def drop(self):
        self.driver.drop_graph(self.name)

    def load(self, fn):
        def _node(ele):
            k, t = self.driver.derive_key_type(ele["labels"])
            iden = ele["id"]
            if "properties" in ele:
                props = ele["properties"]
            else:
                props = self._np
            return ReservedNode(k, t, id=iden, **props)
        data = []
        with open(fn) as f:
            data = json.load(f)
        for d in data:
            if d["type"] == "relationship":
                n = _node(d["start"])
                v = _node(d["end"])
                t = d["label"]
                props = d["properties"]
                iden = d["id"]
                self.driver.add_edge(n, v, t, id=iden, **props)
            elif d["type"] == "node":
                self.driver.add_node(_node(d))
            else:
                raise ValueError(f'{d["type"]} isnt known.')
        self.driver.submit(log=False)

    def save(self,out_fn):
        data = self.driver.export(self.name).splitlines()
        txt = "["
        for index,l in enumerate(data):
            txt += l
            if index < len(data) -1:
                txt += ","
        txt += "]"
        data = json.loads(txt)
        with open(out_fn, 'w') as outfile:
            json.dump(data, outfile)
        return out_fn

    def _create_text_index(self,name,labels,on):
        if "graph_name" not in on:
            on.append("graph_name")
        return self.driver.create_text_index(name,labels,on)
    
    def _add_node_gn(self, node):
        if node is not None:
            gnd = self._np
            node.update(gnd)
            return node
        return None
