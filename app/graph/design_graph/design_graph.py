import types
import re
import json
from rdflib import RDF,DCTERMS
from app.graph.utility.model.model import model
from app.graph.design_graph.gds.project import ProjectBuilder
from app.graph.design_graph.gds.procedures import Procedures
from app.graph.utility.graph_objects.edge import Edge
from app.graph.utility.graph_objects.reserved_node import ReservedNode

def _add_predicate(obj, pred):
    method_name = f'get_{pred.split("/")[-1].lower()}'
    def produce_get_predicate(pred):
        def produce_get_predicate_inner(self, subject=None,predicate="ALL"):
            return self._edge_query(n=subject, e=pred,predicate=predicate)
        return produce_get_predicate_inner
    obj.__dict__[method_name] = types.MethodType(
        produce_get_predicate(pred), obj)


def _add_object(obj, subject):
    method_name = f'get_{subject.split("/")[-1].lower()}'

    def produce_get_subject(subject):
        def produce_get_subject_inner(self,predicate="ALL"):
            derived = ([subject] + [n[1]["key"]
                       for n in model.get_derived(subject)])
            return self._node_query(derived,predicate=predicate)
        return produce_get_subject_inner
    obj.__dict__[method_name] = types.MethodType(
        produce_get_subject(subject), obj)

nv_has_seq = str(model.identifiers.predicates.has_sequence)

class DesignGraph:
    def __init__(self, driver, name):
        if not isinstance(name, list):
            name = [name]
        self.name = name
        self.driver = driver
        self.procedure = Procedures(self)
        self.project = ProjectBuilder(self)

        for c in model.get_classes(False):
            _add_object(self, c[1]["key"])
        for p in model.get_properties():
            _add_predicate(self, p[1]["key"])

    def drop(self):
        self.driver.remove_graph(self.name)

    def nodes(self, n=None, **kwargs):
        return self._node_query(n,**kwargs)

    def edges(self, n=None, v=None, e=None, directed=True, 
              exclusive=False,predicate="ALL"):
        return self._edge_query(n=n, v=v, e=e, directed=directed, 
                                exclusive=exclusive,predicate=predicate)

    def add_node(self,key,type,sequence=None,description=None,**kwargs):
        if "graph_name" not in kwargs:
            kwargs["graph_name"] = self.name
        if sequence is not None:
            if isinstance(sequence,list):
                assert(len(sequence) == 1)
                sequence = sequence[0]
            kwargs[nv_has_seq] = sequence.upper()
        if description is not None:
            if not isinstance(description,list):
                description = [description]
            kwargs[DCTERMS.description] = description
        if "name" not in kwargs:
            if hasattr(key,"name"):
                name = key.name
            else:
                name = _get_name(key)
            kwargs["name"] = name
            
        n = self.driver.add_node(key,type,**kwargs)
        self.driver.submit()
        return n
        
    def add_edges(self,edges):
        for edge in edges:
            if isinstance(edge,Edge):
                n = edge.n
                v = edge.v
                e = edge.get_type()
                props = edge.get_properties()
            elif len(edge) == 4:
                n,v,e,props = edge
            else:
                n,v,e = edge
                props = {}
            if "graph_name" not in props:
                props["graph_name"] = self.name
            if "graph_name" not in n.get_properties():
                n.add_property("graph_name",self.name)
            if "graph_name" not in v.get_properties():
                v.add_property("graph_name",self.name)
            self.driver.add_edge(n,v,e,**props)
        self.driver.submit()

    def remove_node(self,nodes):
        if not isinstance(nodes,list):
            nodes = [nodes]
        for node in nodes:
            if "graph_name" not in node.get_properties():
                node.update({"graph_name" : self.name})
            self.driver.remove_node(node)
        self.driver.submit()

    def remove_edges(self,edges):
        if not isinstance(edges,list):
            edges = [edges]
        for edge in edges:
            if isinstance(edge,Edge):
                n = edge.n
                v = edge.v
                e = edge.get_type()
                props = edge.get_properties()
            elif len(edge) == 4:
                n,v,e,props = edge
            else:
                n,v,e = edge
                props = {}
            if "graph_name" not in props:
                props["graph_name"] = self.name
            if "graph_name" not in n.get_properties():
                n.add_property("graph_name",self.name)
            if "graph_name" not in v.get_properties():
                v.add_property("graph_name",self.name)
            self.driver.remove_edge(n,v,e,**props)
        self.driver.submit()

    def count_edges(self,e_type):
        return self.driver.count_edges(e_type)

    def duplicate_node(self,old,new,graph_name):
        self.driver.duplicate_node(old,new,graph_name)

    def replace_node(self,old,key,properties):
        def _remove_gn(props):
            props = props.copy()
            props["graph_name"] = [n for n in props["graph_name"] 
                                   if n not in self.name]
            return props
        
        def _replace_edge_properties(edge):
            e_props = _remove_gn(edge.properties)
            if e_props["graph_name"] == []:
                self.driver.remove_edge(edge.n,edge.v,
                                        edge.get_type(),
                                        **edge.properties)
            else:
                self.driver.replace_edge_property(edge,e_props)

        def _new_edge(n,v,e,properties):
            properties["graph_name"] = self.name
            self.driver.add_edge(n,v,e,**properties)
        
        def _swap_edges(old_res,new_res):
            for edge in self.edges(n=old_res):
                _new_edge(new_res,edge.v,edge.get_type(),edge.properties.copy())
                _replace_edge_properties(edge)
            for edge in self.edges(v=old_res):
                _new_edge(edge.n,new_res,edge.get_type(),edge.properties.copy())
                _replace_edge_properties(edge)


        properties["graph_name"] = self.name
        properties["name"] = _get_name(key)
        if nv_has_seq in properties:
            properties[nv_has_seq] = properties[nv_has_seq].upper()
        res = self._node_query(old)
        assert(len(res) == 1)
        res = res[0]
        new_res = [r for r in self.driver.node_query(key) 
                   if not isinstance(r,ReservedNode)]

        # Node is already in the network.
        if len(new_res) > 0:
            assert(len(new_res) == 1)
            new_res = new_res[0]
            # Add graph name to existing node
            if len(list(set(self.name) & set(new_res.graph_name))) == 0:
                new_res.properties["graph_name"] += self.name
                self.driver.replace_node_property(res,new_res)
            _swap_edges(res,new_res)
            # Remove old node
            if res.graph_name == self.name:
                self.driver.remove_node(res)
            self.driver.submit()
        elif res.graph_name == self.name:
            del properties["graph_name"]
            self.driver.replace_node_label(old,key,graph_name=self.name,
                                           new_props=properties)
            self.driver.submit()
        else:
            new = self.driver.add_node(key,res.get_type(),**properties)
            _swap_edges(res,new)
            res.properties = _remove_gn(res.properties)
            self.driver.replace_node_property(res,new)
            self.driver.submit()
        
    def replace_label(self,old,new):
        new_props = {"name" : _get_name(new)}
        self.driver.replace_node_label(old,new,new_props=new_props,
                                       graph_name=self.name)
        self.driver.submit()
        
    def get_children(self, node,predicate="ALL"):
        cp = model.get_child_predicate()
        return self._edge_query(n=node, e=cp,predicate=predicate)

    def get_parents(self, node):
        cp = model.get_child_predicate()
        return self._edge_query(v=node, e=cp)

    def get_by_type(self,types):
        return self._node_query(types)

    def get_entity_depth(self, subject):
        def _get_class_depth(s, depth):
            parent = self.get_parents(s)
            if parent == []:
                return depth
            depth += 1
            c_identifier = parent[0].n
            return _get_class_depth(c_identifier, depth)
        return _get_class_depth(subject, 0)

    def get_root_entities(self):
        roots = []
        for node in self.get_entity():
            if self.get_parents(node) == []:
                roots.append(node)
        return roots

    def get_leaf_entities(self):
        roots = []
        for node in self.get_entity():
            if self.get_children(node) == []:
                roots.append(node)
        return roots
        
    def get_interactions(self,node=None,e_type=None,predicate="ALL"):
        s = model.identifiers.objects.interaction
        derived = ([s] + [n[1]["key"] for n in model.get_derived(s)])
        return self._edge_query(n=derived,v=node,e=e_type,
                                predicate=predicate)

    def get_interaction_elements(self,interaction,e_type=None,predicate="ALL"):
        if e_type is None:
            model_code = model.get_class_code(interaction.get_type())
            inp,out = model.interaction_predicates(model_code)
            e_type = [str(i[1]["key"]) for i in inp]
            e_type += [str(o[1]["key"]) for o in out]
            
        return self._edge_query(n=interaction,e=e_type,
                                predicate=predicate)

    def get_interaction_io(self, subject,predicate="ALL"):
        inputs = []
        outputs = []
        d_predicate = model.identifiers.predicates.direction
        i_predicate = model.identifiers.objects.input
        o_predicate = model.identifiers.objects.output
        for edge in self._edge_query(n=subject,predicate=predicate):
            e_type = edge.get_type()
            model_code = model.get_class_code(e_type)
            for d in [d[1] for d in model.search((model_code, d_predicate, None))]:
                d, d_data = d
                if d_data["key"] == i_predicate:
                    inputs.append(edge)
                elif d_data["key"] == o_predicate:
                    outputs.append(edge)
                else:
                    raise ValueError(
                        f'{subject} has direction not input or output')
        return inputs, outputs

    def get_interaction_directions(self,interaction):
        icc = model.get_class_code(interaction.get_type()) 
        idir = model.get_interaction_direction(icc)
        if idir == []:
            return []
        assert(len(idir) == 1)
        return idir[0]

    def get_isolated_nodes(self,predicate="ALL"):
        if None in self.name:
            return []
        return self.driver.get_isolated_nodes(graph_name=self.name,predicate=predicate)
        
    def get_consists_of(self,interaction):
        co = self.edges(interaction,e=model.identifiers.predicates.consists_of)
        assert(len(co) == 1)
        elements = []
        next_node = co[0].v
        while True:
            res = self._edge_query(n=next_node)
            f = [c for c in res if str(RDF.first) in c.get_type()]
            r = [c for c in res if str(RDF.rest) in c.get_type()]
            if len(f) != 1 or len(r) != 1:
                raise ValueError(f'{co[0]} is a malformed list.')
            elements += res
            r = r[0]
            if str(RDF.nil) in r.v.get_labels():
                break
            next_node = r.v
        return elements

    def resolve_list(self, list_node,predicate="ANY"):
        elements = []
        next_node = list_node
        while True:
            res = self._edge_query(n=next_node,predicate=predicate)
            f = [c for c in res if str(RDF.first) in c.get_type()]
            r = [c for c in res if str(RDF.rest) in c.get_type()]
            if len(f) != 1 or len(r) != 1:
                raise ValueError(f'{list_node} is a malformed list.')
            elements.append(f[0])
            r = r[0]
            if str(RDF.nil) in r.v.get_labels():
                break
            next_node = r.v
        return elements
    
    def position_walk(self):
        pos_proj_name = "-".join(self.name) + "_position_projection"
        sources = self.project.position(pos_proj_name)
        paths = self.procedure.dfs(pos_proj_name,sources)
        return [p["path"] for p in paths]
            
    def get_project_preset_names(self):
        return self.project.get_presets()

    def get_projected_names(self):
        return self.project.get_projected_names()

    def get_project_graph(self, name):
        return self.project.get_graph(name)

    def export(self, out_name):
        res = self.driver.export(self.name)
        res_l = []
        for r in res.splitlines():
            res_l.append(json.loads(r))
        with open(out_name, 'w') as f:
            json.dump(res_l, f)
        return out_name

    def _node_query(self, n=None,predicate="ALL", **kwargs):
        if None in self.name:
            return []
        return self.driver.node_query(n, predicate=predicate, graph_name=self.name, **kwargs)

    def _edge_query(self, n=None, e=None, v=None, predicate="ALL", **kwargs):
        if None in self.name:
            return []
        props = {"graph_name": self.name}
        return self.driver.edge_query(n=n, v=v, e=e,
                                      e_props=props, n_props=props, v_props=props,
                                      predicate=predicate, **kwargs)


def _get_name(subject):
    split_subject = _split(subject)
    if split_subject[-1].isdigit():
        return split_subject[-2]
    elif len(split_subject[-1]) == 3 and _isfloat(split_subject[-1]):
        return split_subject[-2]
    else:
        return split_subject[-1]


def _split(uri):
    return re.split('#|\/|:', uri)


def _isfloat(x):
    try:
        float(x)
        return True
    except ValueError:
        return False