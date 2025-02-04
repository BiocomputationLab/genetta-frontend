import os
from graphdatascience import GraphDataScience
from graphdatascience.error.unable_to_connect import UnableToConnectError
from neo4j.graph import Node as NeoNode
from neo4j.graph import Relationship
from neo4j.exceptions import DatabaseError
from neo4j.exceptions import ClientError
import copy
import time

from app.graph.utility.graph_objects.node import Node
from app.graph.utility.graph_objects.edge import Edge
from app.graph.utility.graph_objects.reserved_node import ReservedNode
from app.graph.utility.graph_objects.reserved_edge import ReservedEdge
from app.graph.neo4j_interface.query_builder import QueryBuilder
from app.graph.neo4j_interface.gds.project import Projection
from app.graph.neo4j_interface.gds.procedures import Procedures
from app.graph.utility.model.model import model


def _connect_db(uri, auth):
    attempts = 1
    while attempts < 10:
        try:
            return GraphDataScience(uri, auth=auth)
        except UnableToConnectError:
            print(f'Attempt: {attempts} to connect to neo4j db.')
            time.sleep(5)
            attempts += 1

    else:
        raise UnableToConnectError("Can't connect to Neo4j database.")


class Neo4jInterface:
    def __init__(self, uri, auth, reserved_names=None, logger=None):
        try:
            self.driver = _connect_db(uri, auth)
        except UnableToConnectError:
            self.driver = None
        self.logger = logger
        self.qry_builder = QueryBuilder(logger=logger)
        self.project = Projection(self)
        self.procedures = Procedures(self)
        if reserved_names is None:
            self._rns = []
        else:
            self._rns = reserved_names

    @property
    def nodes(self):
        for node in self.node_query():
            yield node

    @property
    def edges(self):
        for edge in self.edge_query():
            yield edge

    def submit(self, log=True):
        for qry_str in self.qry_builder.generate(log=log):
            self._run(qry_str)

    def add_node(self, key, ntype=None, **kwargs):
        n = self._node(key, ntype, kwargs)
        if "graph_name" not in n.properties:
            raise ValueError("Graph Name property required.")
        if self.qry_builder.is_node_staged(n):
            return n
        q_nodes = self.node_query(n)
        if len(list(set(self._rns) & set(n["graph_name"]))) > 0:
            for node in q_nodes:
                # The node for the reserved graph is already present.
                if len(_intersection(self._rns, node["graph_name"])) > 0:
                    return n
            self.qry_builder.add_create_node(n)
            return n
        q_nodes = [n for n in q_nodes if len(
            _intersection(self._rns, n["graph_name"])) == 0]
        if q_nodes != []:
            for q_node in q_nodes:
                q_node_props = q_node.get_properties()
                n_props = copy.deepcopy(n.get_properties())
                if q_node_props == n_props:
                    continue
                new_props = self._new_props(q_node_props, n_props)
                if new_props == {} or list(new_props.keys()) == ["name"]:
                    continue
                self.qry_builder.add_match_node(q_node)
                self.qry_builder.add_set_node(n, new_props)
                return n
        else:
            self.qry_builder.add_create_node(n)
        return n

    def add_edge(self, n, v, e, **kwargs):
        def validate_node(node):
            if not isinstance(node, Node):
                raise ValueError(f'{node} must be of type Node')
            if "graph_name" not in node.properties:
                raise ValueError(f"{node} - Graph Name property required.")
        n = self.add_node(n)
        v = self.add_node(v)
        validate_node(n)
        validate_node(v)
        e = self._edge(n, v, e, kwargs)
        if "graph_name" not in e.properties:
            raise ValueError("Graph Name property required.")

        if self.qry_builder.is_edge_staged(e):
            return e
        q_edges = self.edge_query(e=e, predicate="ANY")
        if len(list(set(self._rns) & set(e["graph_name"]))) > 0:
            for q_edge in q_edges:
                # The node for the reserved graph is already present.
                if len(_intersection(self._rns, q_edge["graph_name"])) > 0:
                    return e
            self.qry_builder.add_create_edge(e)
            return e
        q_edges = [e for e in q_edges if len(
            _intersection(self._rns, e["graph_name"])) == 0]
        if q_edges != []:
            for q_edge in q_edges:
                q_edge_props = q_edge.get_properties()
                e_props = copy.deepcopy(e.get_properties())
                if q_edge_props == e_props:
                    continue
                new_props = self._new_props(q_edge_props, e_props)
                if new_props == {} or list(new_props.keys()) == ["name"]:
                    continue
                self.qry_builder.add_match_edge(q_edge)
                self.qry_builder.add_set_edge(e, new_props)
                return e
        else:
            self.qry_builder.add_create_edge(e)
        return e

    def remove_edge(self, n, v, e, **kwargs):
        edge = self._edge(n, v, e, kwargs)
        self.qry_builder.add_match_edge(edge)
        self.qry_builder.add_remove_edge(edge)

    '''
    def remove_node(self, node, use_id=False):
        self.qry_builder.add_match_node(node, use_id)
        self.qry_builder.add_remove_node(node)
    '''
    
    def remove_node(self, node=None, use_id=False,key=None,
                    type=None,properties=None):
        if node is None:
            if properties is None:
                props = {}
            else:
                props = properties
            node = Node(key,type,**props)
        self.qry_builder.add_match_node(node, use_id)
        self.qry_builder.add_remove_node(node)

    def duplicate_node(self,old,new,graph_name):
        qry = self.qry_builder.duplicate_node(old,new,graph_name)
        return self._run(qry)

    def replace_node_label(self, old_label, new_label, new_props=None, **kwargs):
        n = Node(old_label, **kwargs)
        self.qry_builder.add_match_node(n)
        if new_props is not None:
            self.qry_builder.add_set_node(n, new_props)
        self.qry_builder.add_replace_node_label(n, old_label, new_label)

    def replace_edge_property(self,edge,new_properties):
        edge = self._edge(edge.n, edge.v, edge.get_type(), edge.properties)
        self.qry_builder.add_match_edge(edge)
        self.qry_builder.add_replace_edge_properties(edge, new_properties)

    def replace_node_property(self,old,new):
        if "graph_name" in new.properties:
            gn_change = list(set(new.properties["graph_name"]) - 
                             set(old.properties["graph_name"]))
        else:
            gn_change = []
        self.qry_builder.add_match_node(old)
        self.qry_builder.add_replace_node_properties(old, old.properties.copy())
        for gn in gn_change:
            if self.logger is not None:
                self.logger.replace_node_property(old,new.properties,[gn])
                self.logger.replace_node(old,new,[gn])
                    

    def set_edge(self, edge, new_properties):
        self.qry_builder.add_match_edge(edge)
        self.qry_builder.add_set_edge(edge, new_properties)

    def add_node_label(self, node, label):
        self.qry_builder.add_match_node(node)
        self.qry_builder.add_add_node_label(node, label)

    def merge_nodes(self,source,merged,properties=None):
        qry = self.qry_builder.merge_nodes(source,merged,
                                           properties=properties)
        return self.run_query(qry)

    def remove_graph(self, graph_name):
        if not isinstance(graph_name, list):
            graph_name = [graph_name]
        for node in self.nodes:
            if "graph_name" not in node.get_properties():
                continue
            gns = node["graph_name"]
            if len(set(graph_name) & set(gns)) == 0:
                continue
            self.qry_builder.add_match_node(node)
            if len(gns) == 1:
                self.qry_builder.add_remove_node(node)
            else:
                self.qry_builder.add_remove_node_property(
                    node, {"graph_name": graph_name})
                for edge in self.edge_query(n=node):
                    props = edge.get_properties()
                    if "graph_name" not in props:
                        continue
                    self.qry_builder.add_match_edge(edge)
                    self.qry_builder.add_remove_edge_property(
                        edge, {"graph_name": graph_name})
        self.submit()
        if self.logger is not None:
            self.logger.remove_graph(graph_name)

    def create_text_index(self, name, labels, on):
        e_indexes = self._run(self.qry_builder.list_text_indexes())
        for ei in e_indexes.iterrows():
            ei = ei[1]
            ei_labels = ei["labelsOrTypes"]
            ei_props = ei["properties"]
            ei_state = ei["state"]
            if (sorted(ei_labels) == sorted(labels) and
                sorted(ei_props) == sorted(on) and
                    ei_state == "ONLINE"):
                return ei["name"]
            if ei["name"] == name:
                self.drop_text_index(name)
                break
        qry = self.qry_builder.create_text_index(name, labels, on)
        try:
            self._run(qry)
        except ClientError:
            pass
        return name

    def drop_text_index(self, name):
        qry = self.qry_builder.drop_text_index(name)
        try:
            return self._run(qry)
        except DatabaseError:
            pass

    def query_text_index(self, index_name, values, graph_names=None,
                         predicate=None, wildcard=False, fuzzy=False,
                         threshold=None):
        qry = self.qry_builder.query_text_index(index_name, values,
                                                graph_names=graph_names,
                                                predicate=predicate,
                                                wildcard=wildcard,
                                                fuzzy=fuzzy,
                                                threshold=threshold)
        df = self._run(qry)
        results = {}
        for row in df.iterrows():
            row = row[1]
            node = row["node"]
            score = row["score"]
            key, r_type = self.derive_key_type(node.labels)
            props = self._go_dict(node)
            score = int(score)*10
            if score > 100:
                score = 100
            results[self._node(key, r_type, props)] = score 
        return results

    def drop_graph(self, graph_name):
        if not isinstance(graph_name, list):
            graph_name = [graph_name]
        qry = self.qry_builder.remove_graph(graph_name)
        return self._run(qry)

    def node_query(self, identity=None, predicate="ALL", **kwargs):
        qry = self.qry_builder.node_query(
            identity, predicate=predicate, **kwargs)
        results = []
        for index, record in self._run(qry).iterrows():
            for k, v in record.items():
                key, r_type = self.derive_key_type(v.labels)
                props = self._go_dict(v)
                results.append(self._node(key, r_type, props))
        return results

    def edge_query(self, n=None, v=None, e=None, n_props={}, v_props={},
                   e_props={}, directed=True, exclusive=False,
                   predicate="ALL"):
        if isinstance(e, Edge):
            if n is None:
                n = e.n
            if v is None:
                v = e.v
            e = e.get_type()
        qry = self.qry_builder.edge_query(n, v, e, n_props.copy(),
                                          v_props.copy(),
                                          e_props.copy(),
                                          directed=directed,
                                          exclusive=exclusive,
                                          predicate=predicate)
        results = []
        for index, record in self._run(qry).iterrows():
            n = record["n"]
            v = record["v"]
            e = record["e"]
            nkey, n_type = self.derive_key_type(n.labels)
            vkey, v_type = self.derive_key_type(v.labels)
            n_props = self._go_dict(n)
            v_props = self._go_dict(v)
            e_props = self._go_dict(e)
            results.append(self._edge(self._node(nkey, n_type, n_props), self._node(
                vkey, v_type, v_props), e.type, e_props))
        return results

    def get_graph_names(self):
        gns = self.node_property("graph_name", distinct=True)
        return list(set(gns))

    def node_property(self, prop_name, distinct=False):
        qry = self.qry_builder.node_property(prop=prop_name, distinct=distinct)
        results = []
        for index, record in self._run(qry).iterrows():
            for k, v in record.items():
                if prop_name in k and v is not None:
                    if isinstance(v, list):
                        results += v
                    else:
                        results.append(v)
        return results

    def node_edge_count(self,graph_name=None):
        n_qry,e_qry = self.qry_builder.node_edge_count(graph_name=graph_name)
        n_v = {rec["label"] : rec["count"] 
               for rec in self.run_query(n_qry)}
        e_v = {rec["label"] : rec["count"] 
               for rec in self.run_query(e_qry)}
        return n_v,e_v

    
    def count_edges(self,e_type):
        qry = self.qry_builder.count_edge(e_type)
        return self.run_query(qry)[0]["count(e)"]
    
    def labels_to_node(self, labels):
        return Node(*self.derive_key_type(labels))

    def get_isolated_nodes(self, predicate="ALL", **kwargs):
        results = []
        qry = self.qry_builder.get_isolated_nodes(
            predicate=predicate, **kwargs)
        for index, record in self._run(qry).iterrows():
            for k, v in record.items():
                key, r_type = self.derive_key_type(v.labels)
                props = self._go_dict(v)
                results.append(self._node(key, r_type, props))
        return results

    def run_query(self, cypher_str):
        results = []

        def _node(item):
            key, r_type = self.derive_key_type(item.labels)
            properties = dict(item).copy()
            properties["id"] = item.id
            return self._node(key, r_type, properties)

        for index, r in self._run(cypher_str).iterrows():
            record = {}
            for k, v in r.items():
                if isinstance(v, NeoNode):
                    record[k] = _node(v)
                elif isinstance(v, Relationship):
                    n = _node(v.start_node)
                    n1 = _node(v.end_node)
                    e_props = self._go_dict(v)
                    record[k] = self._edge(n, n1, v.type, e_props)
                else:
                    record[k] = v
            results.append(record)
        return results

    def export(self, graph_name):
        qry = self.qry_builder.export(graph_name)
        res = self._run(qry)["data"][0]
        return res

    def derive_key_type(self, labels):
        labels = list(labels)
        if "None" in labels:
            k = [l for l in labels if l != "None"]
            return k[0], "None"
        res = model.are_classes(labels)
        n = zip(labels, res)
        k = []
        t = []
        for lab, ac in n:
            if ac:
                t.append(lab)
            else:
                k.append(lab)
        if len(k) == 1:
            k = k[0]
        if len(t) == 1:
            t = t[0]
        if len(k) == 0:
            k = t
        if t == []:
            return k, None
        return k, t

    def _run(self, cypher_str):
        if len(cypher_str) == 0:
            #print("WARN:: Empty Cypher Query Entered.")
            return []
        if self.driver is None:
            print("WARN:: No connection to neo4j graph.")
        return self.driver.run_cypher(cypher_str)

    def _node(self, name, ntype=None, properties=None):
        if properties is None:
            properties = {}
        if isinstance(name, Node):
            n = name
            n.update(properties)
            if self._is_reserved(n):
                return ReservedNode(n.get_key(), n.get_type(), **n.get_properties())
        elif self._is_reserved(props=properties):
            n = ReservedNode(name, ntype, **properties)
        else:
            n = Node(name, ntype, **properties)

        if n in self.qry_builder.nodes:
            on = n
            n = self.qry_builder.nodes[n].graph_object
            if n.type == "None":
                n.type = on.type
            if "graph_name" in properties:
                del properties["graph_name"]
            n.update(properties)
        return n

    def _edge(self, n, v, e, properties):
        if self._is_reserved(props=properties):
            return ReservedEdge(n, v, e, **properties)
        return Edge(n, v, e, **properties)

    def _is_reserved(self, go=None, props=None):
        if go is not None:
            props = go.properties
        if "graph_name" not in props:
            return False
        if len(list(set(self._rns) & set(props["graph_name"]))) > 0:
            return True
        return False

    def _go_dict(self, go):
        props = dict(go)
        props["id"] = go.element_id
        return props

    def _new_props(self, old_props, new_props):
        final_props = {}
        for k, v in new_props.items():
            if k in old_props:
                if isinstance(v, list):
                    ind = 0
                    while ind < len(v):
                        item = v[ind]
                        if item in old_props[k]:
                            v.pop(ind)
                        else:
                            ind += 1
                    if len(v) > 0:
                        final_props[k] = v
                else:
                    final_props[k] = v
            else:
                final_props[k] = v
        return final_props


def _intersection(l1, l2):
    return list(set(l1) & set(l2))
