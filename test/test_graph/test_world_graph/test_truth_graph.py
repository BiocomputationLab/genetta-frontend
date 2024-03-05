import sys
import os
import unittest
import networkx as nx
sys.path.insert(0, os.path.join(".."))
sys.path.insert(0, os.path.join("..",".."))
sys.path.insert(0, os.path.join("..","..",".."))
sys.path.insert(0, os.path.join("..","..","..",".."))
sys.path.insert(0, os.path.join("..","..","..","..",".."))
from app.graph.world_graph import WorldGraph
from app.converter.sbol_convert import convert
from app.graph.truth_graph.modules.abstract_module import AbstractModule
from app.graph.truth_graph.modules.synonym import SynonymModule
from app.graph.truth_graph.modules.interaction import InteractionModule
from app.graph.truth_graph.modules.module import InteractionModuleModule
from app.graph.truth_graph.modules.derivative import DerivativeModule
from app.graph.utility.graph_objects.reserved_edge import ReservedEdge
from app.graph.utility.graph_objects.reserved_node import ReservedNode
from app.graph.utility.model.model import model

curr_dir = os.path.dirname(os.path.realpath(__file__))
dfn = os.path.join(curr_dir,"..","..","files","nor_full.xml")
confidence = str(model.identifiers.external.confidence)
db_host = os.environ.get('NEO4J_HOST', 'localhost')
db_port = os.environ.get('NEO4J_PORT', '7687')
db_auth = os.environ.get('NEO4J_AUTH', "neo4j/Radeon12300")
db_auth = tuple(db_auth.split("/"))
uri = f'neo4j://{db_host}:{db_port}'
login_graph_name = "login_manager"

class TestTruthGraph(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.wg = WorldGraph(uri,db_auth,reserved_names=[login_graph_name])
        self.tg = self.wg.truth
        self.module = AbstractModule(self.tg)

    @classmethod
    def tearDownClass(self):
        pass

    def test_export_load(self):
        out_fn = "output.xml"
        pre_nodes = self.tg.nodes()
        pre_edges = self.tg.edges()

        self.tg.export(out_fn)

        self.wg.remove_design(self.tg.name)
        self.assertEqual(self.tg.nodes(),[])
        self.assertEqual(self.tg.edges(),[])

        self.tg.load(out_fn)

        post_nodes = self.tg.nodes()
        post_edges = self.tg.edges()

        ndiff = list(set(post_nodes) - set(pre_nodes))
        ediff = list(set(post_edges) - set(pre_edges))

        self.assertEqual(ndiff,[])
        self.assertEqual(ediff,[])

    def test_export_load(self):
        test_fn = "test_export_load.json"
        pre_nodes = self.tg.nodes()
        pre_edges = self.tg.edges()
        self.tg.export(test_fn)
        self.tg.drop()
        mid_nodes = self.tg.nodes()
        mid_edges = self.tg.edges()
        self.assertEqual(mid_nodes,[])
        self.assertEqual(mid_edges,[])
        self.tg.load(test_fn)
        post_nodes = self.tg.nodes()
        post_edges = self.tg.edges()
        self.assertCountEqual(pre_nodes,post_nodes)
        self.assertCountEqual(pre_edges,post_edges)
        os.remove(test_fn)

    def test_text_index(self):
        qry_vals = {"name" : "ptet"}
        res = self.tg.query_text_index(qry_vals,fuzzy=True)
        self.assertIn("https://synbiohub.programmingbiology.org/public/Cello_Parts/pTet/1",
                      [k.get_key() for k in res])

        pe = model.identifiers.objects.promoter
        i = model.identifiers.objects.synonym
        props = {"graph_name" : self.tg.name,"http://purl.org/dc/terms/description":"ptec"}
        n1 = ReservedNode("https://synbiohub.programmingbiology.org/public/Cello_Parts/ptet/1",pe,**props)
        n2 = ReservedNode("https://synbiohub.programmingbiology.org/public/Cello_Parts/ptet_syn/1",i,**props)
        edge = ReservedEdge(n1,n2,model.identifiers.external.synonym,**props)
        self.module.positive(edge)
        res2 = self.tg.query_text_index(qry_vals,fuzzy=True)
        matches = []
        for node,score in res2.items():
            if node in res:
                continue
            matches.append(node)
        self.assertEqual(len(matches),1)
        self.assertEqual(n1,matches[0])
        self.module.negative(edge)
        qry_vals = {"name" : "LuxR_sens"}
        res = self.tg.query_text_index(qry_vals,wildcard=True,fuzzy=True)
        self.assertGreater(len(res),0)

    def test_graph_merges(self):
        d_graph = self.tg.derivatives.get()
        s_graph = self.tg.synonyms.get()
        c_graph = d_graph + s_graph
        self.assertLess(len(c_graph),len(d_graph)+len(s_graph))
        seen_keys = []
        for n in c_graph.nodes():
            self.assertFalse(n.get_key() in seen_keys)
            seen_keys.append(n.get_key())


class TestModule(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.wg = WorldGraph(uri,db_auth,reserved_names=[login_graph_name])
        self.tg = self.wg.truth
        self.module = AbstractModule(self.tg)

    @classmethod
    def tearDownClass(self):
        pass

    def setUp(self):
        pe = model.identifiers.objects.physical_entity
        i = model.identifiers.objects.interaction
        self.props = {"graph_name" : self.tg.name}
        self.n1 = ReservedNode("PE1",pe,**self.props)
        self.n2 = ReservedNode("I1",i,**self.props)
        self.n3 = ReservedNode("PE2",pe,**self.props)
        self.n4 = ReservedNode("I2",i,**self.props)
        self.n5 = ReservedNode("I2_syn",i,**self.props)
        self.n6 = ReservedNode("PE3",pe,**self.props)
        self.n7 = ReservedNode("PE4",pe,**self.props)
        self.n8 = ReservedNode(model.identifiers.objects.dna,**self.props)

        self.edge = ReservedEdge(self.n1,self.n2,model.identifiers.predicates.repressor,**self.props)
        self.edge2 = ReservedEdge(self.n3,self.n2,model.identifiers.predicates.repressed,**self.props)
        self.edge3 = ReservedEdge(self.n3,self.n4,model.identifiers.predicates.activator,**self.props)
        self.edge4 = ReservedEdge(self.n2,self.n4,model.identifiers.predicates.activator,**self.props)
        self.edge5 = ReservedEdge(self.n4,self.n5,model.identifiers.external.synonym,**self.props)

        self.edge6 = ReservedEdge(self.n1,self.n5,model.identifiers.predicates.repressor,**self.props)
        self.edge7 = ReservedEdge(self.n3,self.n5,model.identifiers.predicates.repressed,**self.props)
        self.edge8 = ReservedEdge(self.n5,self.n6,model.identifiers.predicates.activator,**self.props)
        self.edge9 = ReservedEdge(self.n5,self.n7,model.identifiers.predicates.activator,**self.props)

        self.edge9 = ReservedEdge(self.n7,self.n8,model.identifiers.external.type,**self.props)
        
        self.edges = [self.edge,self.edge2,self.edge3,self.edge4,
                    self.edge5,self.edge6,self.edge7,self.edge8,self.edge9]
        for e in self.edges:
            self.tg.driver.remove_edge(e.n,e.v,e.get_type())
            self.tg.driver.remove_node(e.n)
            self.tg.driver.remove_node(e.v)
        self.tg.driver.submit()

    def tearDown(self):
        for e in self.edges:
            self.tg.driver.remove_edge(e.n,e.v,e.get_type())
            self.tg.driver.remove_node(e.n)
            self.tg.driver.remove_node(e.v)
        self.tg.driver.submit()


    def _edge_equal(self,actual,expected):
        expected.n.properties["graph_name"] = self.tg.name
        expected.n.graph_name = self.tg.name
        expected.v.properties["graph_name"] = self.tg.name
        expected.v.graph_name = self.tg.name
        expected.properties["graph_name"] = self.tg.name
        expected.graph_name = self.tg.name
        self.assertEqual(actual,expected)


    def test_positive(self):
        self.module.positive(self.edge)
        e = self.module.get(self.edge)
        self.assertIsInstance(e,ReservedEdge)
        self._edge_equal(e,self.edge)
        conf = e[confidence]
        self.assertEqual(conf,self.module._standard_modifier)
    
    def test_positive_increment(self):
        self.module.positive(self.edge)
        e = self.module.get(self.edge)
        self.assertIsInstance(e,ReservedEdge)
        self._edge_equal(e,self.edge)
        conf = e[confidence]
        self.assertEqual(conf,self.module._standard_modifier)

        self.module.positive(self.edge)
        e = self.module.get(self.edge)
        self.assertIsInstance(e,ReservedEdge)
        self._edge_equal(e,self.edge)
        conf = e[confidence]
        self.assertEqual(conf,self.module._standard_modifier*2)

        self.module.positive(self.edge)
        e = self.module.get(self.edge)
        self.assertIsInstance(e,ReservedEdge)
        self._edge_equal(e,self.edge)
        conf = e[confidence]
        self.assertEqual(conf,self.module._standard_modifier*3)

    def test_positive_node_only(self):
        self.module.positive(self.edge)
        e = self.module.get(self.edge)
        self.assertIsInstance(e,ReservedEdge)
        self._edge_equal(e,self.edge)
        conf = e[confidence]
        self.assertEqual(conf,self.module._standard_modifier)


        self.module.positive(self.edge2)
        e = self.module.get(self.edge2)
        self.assertIsInstance(e,ReservedEdge)
        self.assertEqual(e,self.edge2)
        conf = e[confidence]
        self.assertEqual(conf,self.module._standard_modifier)

        self.module.positive(self.edge3)
        e = self.module.get(self.edge3)
        self.assertIsInstance(e,ReservedEdge)
        self.assertEqual(e,self.edge3)
        conf = e[confidence]
        self.assertEqual(conf,self.module._standard_modifier)

        self.module.positive(self.edge4)
        e = self.module.get(self.edge4)
        self.assertIsInstance(e,ReservedEdge)
        self.assertEqual(e,self.edge4)
        conf = e[confidence]
        self.assertEqual(conf,self.module._standard_modifier)
        
    def test_negative(self):
        self.module.negative(self.edge)
        e = self.module.get(self.edge)
        self.assertIsNone(e)

        conf_count = 0
        for i in range(0,5):
            self.module.positive(self.edge)
            conf_count += self.module._standard_modifier

        self.module.negative(self.edge)
        conf_count -= self.module._standard_modifier
        e = self.module.get(self.edge)
        self.assertIsInstance(e,ReservedEdge)
        self._edge_equal(e,self.edge)
        conf = e[confidence]
        self.assertEqual(conf,conf_count)
    
    def test_negative_increment(self):        
        conf_count = 0
        for i in range(0,5):
            self.module.positive(self.edge)
            conf_count += self.module._standard_modifier

        self.module.negative(self.edge)
        conf_count -= self.module._standard_modifier
        e = self.module.get(self.edge)
        self.assertIsInstance(e,ReservedEdge)
        self._edge_equal(e,self.edge)
        conf = e[confidence]
        self.assertEqual(conf,conf_count)

        self.module.negative(self.edge)
        conf_count -= self.module._standard_modifier
        e = self.module.get(self.edge)
        self.assertIsInstance(e,ReservedEdge)
        self._edge_equal(e,self.edge)
        conf = e[confidence]
        self.assertEqual(conf,conf_count)

        self.module.negative(self.edge)
        conf_count -= self.module._standard_modifier
        e = self.module.get(self.edge)
        self.assertIsInstance(e,ReservedEdge)
        self._edge_equal(e,self.edge)
        conf = e[confidence]
        self.assertEqual(conf,conf_count)
    
    def test_negative_node_only(self):        
        conf_count = 0
        for i in range(0,2):
            self.module.positive(self.edge)
            self.module.positive(self.edge2)
            self.module.positive(self.edge3)
            self.module.positive(self.edge4)
            conf_count += self.module._standard_modifier
        conf_count -= self.module._standard_modifier


        self.module.negative(self.edge2)
        e = self.module.get(self.edge2)
        self.assertIsInstance(e,ReservedEdge)
        self.assertEqual(e,self.edge2)
        conf = e[confidence]
        self.assertEqual(conf,conf_count)

        self.module.negative(self.edge3)
        e = self.module.get(self.edge3)
        self.assertIsInstance(e,ReservedEdge)
        self.assertEqual(e,self.edge3)
        conf = e[confidence]
        self.assertEqual(conf,conf_count)

        self.module.negative(self.edge4)
        e = self.module.get(self.edge4)
        self.assertIsInstance(e,ReservedEdge)
        self.assertEqual(e,self.edge4)
        conf = e[confidence]
        self.assertEqual(conf,conf_count)

    def test_lower_threshold(self):
        d = self.wg.get_design("test_lower_threshold")
        n = self.edge.n.duplicate()
        v = self.edge.v.duplicate()
        n.remove(self.props)
        v.remove(self.props)
        edges = [(n,v,self.edge.get_type(),{})]
        d.add_edges(edges)
        self.module.positive(self.edge)
        self.module.negative(self.edge)

        e = self.module.get(self.edge)
        self.assertIsNone(e)
        res = d.edges(edges[0][0],edges[0][1],edges[0][2])
        self.assertEqual(len(res),1)
        self.assertEqual(self.edge,res[0])
        self.wg.remove_design("test_lower_threshold")

    def test_with_designs(self):
        self.wg.remove_design("test_with_designs")
        dg = self.wg.get_design("test_with_designs")
        edges = []
        for e in self.edges:
            n = e.n.duplicate()
            v = e.v.duplicate()
            n.remove(self.props)
            v.remove(self.props)
            edges.append((n,v,e.get_type(),{}))
        dg.add_edges(edges)
        pn = dg.nodes()
        self.module.positive(self.edge)
        self.module.negative(self.edge)
        pon = dg.nodes()
        self.assertCountEqual(pn,pon)

        res = self.module.get(self.edge)
        self.assertIsNone(res)

        self.wg.remove_design("test_with_designs")

class TestSynonymModule(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.wg = WorldGraph(uri,db_auth,reserved_names=[login_graph_name])
        self.tg = self.wg.truth
        self.module = SynonymModule(self.tg)
        self.props = {"graph_name" : self.tg.name}

    @classmethod
    def tearDownClass(self):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def _edge_equal(self,actual,expected):
        expected.n.properties["graph_name"] = self.tg.name
        expected.n.graph_name = self.tg.name
        expected.v.properties["graph_name"] = self.tg.name
        expected.v.graph_name = self.tg.name
        expected.properties["graph_name"] = self.tg.name
        expected.graph_name = self.tg.name
        self.assertEqual(actual,expected)
    
    def _assert_edge_count_equal(self,actuals,expecteds):
        for e in expecteds:
            e.n.properties["graph_name"] = self.tg.name
            e.n.graph_name = self.tg.name
            e.v.properties["graph_name"] = self.tg.name
            e.v.graph_name = self.tg.name
            e.properties["graph_name"] = self.tg.name
            e.graph_name = self.tg.name

    def test_synonym_positive(self):
        node = ReservedNode("https://test_resource/BBa_test_K823003567/1",model.identifiers.objects.physical_entity,**self.props)
        vertex = ReservedNode("test_name",**self.props)
        edge = ReservedEdge(node,vertex,model.identifiers.external.synonym,**self.props)
        self.tg.remove_edges(edge)
        self.tg.driver.submit()
        

        self.module.positive(node,vertex)
        res = self.module.get(node,vertex,threshold=5)
        res = list(res.edges())
        self.assertTrue(len(res) == 1)
        res = res[0]
        self._edge_equal(res,edge)
        self.assertEqual(res.confidence,5)
        self.module.positive(node,vertex)
        res = self.module.get(node,vertex,threshold=5)
        res = list(res.edges())
        self.assertTrue(len(res) == 1)
        res = res[0]
        self._edge_equal(res,edge)
        self.assertEqual(res.confidence,10)

        node1 = ReservedNode("https://test_resource/pveg/1",name="pveg",**self.props)
        vertex1 = ReservedNode("BBa_test_K823003",**self.props)
        self.module.positive(node1,vertex1)
        res = self.module.get(node,vertex,threshold=5)
        res = list(res.edges())
        self.assertTrue(len(res) == 1)
        res = res[0]
        self._edge_equal(res,edge)
        self.assertEqual(res.confidence,10)

        self.module.negative(node,vertex)
        self.module.negative(node,vertex)
        self.module.negative(node,vertex)

    def test_synonym_get(self):
        node = ReservedNode("https://test_resource/BBa_test_K823003/1",model.identifiers.objects.physical_entity,**self.props)
        vertex = ReservedNode("test_name",**self.props)
        edge = ReservedEdge(node,vertex,model.identifiers.external.synonym,**self.props)
        self.tg.remove_edges(edge)
        self.tg.driver.submit()
        

        self.module.positive(node,vertex)
        res = self.module.get(node,vertex,threshold=5)
        res = list(res.edges())
        self._edge_equal(res[0],edge)

        node1 = ReservedNode("https://test_resource/test/1",model.identifiers.objects.physical_entity,**self.props)
        vertex1 = ReservedNode("test_name",**self.props)
        edge1 = ReservedEdge(node1,vertex1,model.identifiers.external.synonym,**self.props)
        self.module.positive(node1,vertex1)

        self._assert_edge_count_equal(res,[edge,edge1])
        self.module.negative(node,vertex)
        self.module.negative(node,vertex)
        self.module.negative(node,vertex)


    def test_synonym_get_canonical(self):
        node = ReservedNode("https://test_resource/BBa_test_K823003/1",model.identifiers.objects.physical_entity,**self.props)
        vertex = ReservedNode("test_name",**self.props)
        edge = ReservedEdge(node,vertex,model.identifiers.external.synonym,**self.props)
        self.tg.remove_edges(edge)
        self.tg.driver.submit()
        

        self.module.positive(node,vertex)
        res = self.module.get(synonym=vertex,threshold=5)
        res = list(res.edges())
        self._edge_equal(res[0],edge)
        self.module.negative(node,vertex)
        self.module.negative(node,vertex)
        self.module.negative(node,vertex)

    def test_synonym_get_canonical_full(self):
        node = ReservedNode("https://test_resource/BBa_test_K823003/1",model.identifiers.objects.physical_entity,**self.props)
        vertex = ReservedNode("https://test_resource/test_synonym/1",**self.props)
        edge = ReservedEdge(node,vertex,model.identifiers.external.synonym,**self.props)
        self.tg.remove_edges(edge)
        self.tg.driver.submit()
        

        self.module.positive(node,vertex)
        res = self.module.get(synonym=vertex,threshold=5)
        res = list(res.edges())
        self._edge_equal(res[0],edge)
        self.module.negative(node,vertex)
        self.module.negative(node,vertex)
        self.module.negative(node,vertex)

    def test_synonym_negative(self):
        node = ReservedNode("https://test_resource/BBa_test_K823003/1",model.identifiers.objects.physical_entity,**self.props)
        vertex = ReservedNode("pveggg",**self.props)
        edge = ReservedEdge(node,vertex,model.identifiers.external.synonym,**self.props)
        self.tg.remove_edges(edge)
        self.tg.driver.submit()

        for i in range(0,2):
            self.module.positive(node,vertex)

        res = self.module.get(node,vertex,threshold=5)
        res = list(res.edges())
        self.assertTrue(len(res),1)
        res = res[0]
        self.assertEqual(res.confidence,10)

        for i in range(0,2):
            self.module.negative(node,vertex)
        
        res = self.module.get(node,vertex,threshold=5)
        res = list(res.edges())
        self.assertEqual(res,[])

        self.module.negative(node,vertex)
        res = self.module.get(node,vertex,threshold=5)
        res = list(res.edges())
        self.assertEqual(res,[])

    def test_get_synonym_subject(self):
        node = ReservedNode("https://test_resource/BBa_test_K823003/1",model.identifiers.objects.physical_entity,**self.props)
        vertex = ReservedNode("pvesg",**self.props)
        edge = ReservedEdge(node,vertex,model.identifiers.external.synonym,**self.props)
        self.tg.remove_edges(edge)
        self.tg.driver.submit()

        for i in range(0,2):
            self.module.positive(node,vertex)

        res = self.module.get(synonym=vertex)
        res = list(res.edges())
        self.assertTrue(len(res),1)
        res = res[0]
        self.assertEqual(res.confidence,10)

class TestInteractionModule(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.wg = WorldGraph(uri,db_auth,reserved_names=[login_graph_name])
        self.tg = self.wg.truth
        self.module = InteractionModule(self.tg)

    @classmethod
    def tearDownClass(self):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def _edge_equal(self,actual,expected):
        expected.n.properties["graph_name"] = self.tg.name
        expected.n.graph_name = self.tg.name
        expected.v.properties["graph_name"] = self.tg.name
        expected.v.graph_name = self.tg.name
        expected.properties["graph_name"] = self.tg.name
        expected.graph_name = self.tg.name
        self.assertEqual(actual,expected)
    
    def test_interaction_positive(self):
        node = ReservedNode("https://test_resource/tetR/1",model.identifiers.objects.dna)
        vertex = ReservedNode("https://test_resource/repression/1",model.identifiers.objects.repression)
        edge = model.identifiers.predicates.repressor
        e_edge = ReservedEdge(vertex,node,model.identifiers.predicates.repressor,graph_name=self.tg.name)
        self.tg.remove_edges(e_edge)
        self.tg.driver.submit()
        
        self.module.positive(vertex,node,edge)
        res = self.module.get(vertex,node,edge,threshold=5)
        edges = list(res.edges())
        self.assertTrue(len(edges) == 1)
        edges = edges[0]
        self._edge_equal(edges,e_edge)
        self.assertEqual(edges.confidence,5)
        self.module.positive(vertex,node,edge)
        res = self.module.get(vertex,node,edge,threshold=5)
        edges = list(res.edges())
        self.assertTrue(len(edges) == 1)
        edges = edges[0]
        self._edge_equal(edges,e_edge)
        self.assertEqual(edges.confidence,10)

        self.module.negative(vertex,node,edge)
        self.module.negative(vertex,node,edge)

    def test_interaction_get(self):
        node = ReservedNode("https://test_resource/test_synonym_get_object1/1",model.identifiers.objects.dna)
        node2 = ReservedNode("https://test_resource/test_synonym_get_object2/1",model.identifiers.objects.dna)
        vertex = ReservedNode("https://test_resource/test_synonym_get_object3/1",model.identifiers.objects.repression)
        edge = model.identifiers.predicates.repressor
        e_edge = ReservedEdge(vertex,node,model.identifiers.predicates.repressor,graph_name=self.tg.name)
        self.tg.remove_edges(e_edge)
        self.tg.driver.submit()
        
        self.module.positive(vertex,node,edge)
        res = self.module.get(vertex,node,edge,threshold=5)
        edges = list(res.edges())
        self._edge_equal(edges[0],e_edge)

    def test_synonym_negative(self):
        node = ReservedNode("https://test_resource/test_synonym_get_object1/1",model.identifiers.objects.dna)
        node2 = ReservedNode("https://test_resource/test_synonym_get_object2/1",model.identifiers.objects.dna)
        vertex = ReservedNode("https://test_resource/test_synonym_get_object3/1",model.identifiers.objects.repression)
        edge = model.identifiers.predicates.repressor
        e_edge = ReservedEdge(vertex,node,model.identifiers.predicates.repressor,graph_name=self.tg.name)
        self.tg.remove_edges(e_edge)
        self.tg.driver.submit()

        for i in range(0,2):
            self.module.positive(vertex,node,edge)

        g = self.module.get(vertex,node,edge,threshold=5)
        edges = list(g.edges())
        self.assertTrue(len(edges),1)
        edges = edges[0]
        self.assertEqual(edges.confidence,10)

        for i in range(0,2):
            self.module.negative(vertex,node,edge)
        
        g = self.module.get(vertex,node,edge,threshold=5)
        edges = list(g.edges())
        self.assertEqual(edges,[])

        self.module.negative(vertex,node,edge)
        g = self.module.get(vertex,node,edge,threshold=5)
        edges = list(g.edges())
        self.assertEqual(edges,[])


    def test_synonym_get_object(self):
        node = ReservedNode("https://test_resource/test_synonym_get_object1/1",model.identifiers.objects.dna)
        node2 = ReservedNode("https://test_resource/test_synonym_get_object2/1",model.identifiers.objects.dna)
        vertex = ReservedNode("https://test_resource/test_synonym_get_object3/1",model.identifiers.objects.repression)
        edge = model.identifiers.predicates.repressor
        e_edge1 = ReservedEdge(vertex,node,model.identifiers.predicates.repressor,graph_name=self.tg.name)
        e_edge2 = ReservedEdge(vertex,node2,model.identifiers.predicates.repressor,graph_name=self.tg.name)
        self.tg.remove_edges(e_edge1)
        self.tg.remove_edges(e_edge2)
        self.tg.driver.submit()

        for i in range(0,2):
            self.module.positive(vertex,node,edge)
            self.module.positive(vertex,node2,edge)


        g = self.module.get(object=node)
        edges = list(g.edges())
        self.assertCountEqual(edges,[e_edge1,e_edge2])

        for i in range(0,2):
            self.module.negative(vertex,node,edge)
            self.module.negative(vertex,node2,edge)
        
        g = self.module.get(vertex,node,edge,threshold=5)
        edges = list(g.edges())
        self.assertEqual(edges,[])
        g = self.module.get(vertex,node2,edge,threshold=5)
        edges = list(g.edges())
        self.assertEqual(edges,[])

        self.module.negative(vertex,node,edge)
        g = self.module.get(vertex,node,edge,threshold=5)
        self.assertEqual(edges,[])
        self.module.negative(vertex,node2,edge)
        g = self.module.get(vertex,node2,edge,threshold=5)
        self.assertEqual(edges,[])
        
class TestDerivativeModule(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.wg = WorldGraph(uri,db_auth,reserved_names=[login_graph_name])
        self.tg = self.wg.truth
        self.module = DerivativeModule(self.tg)
        self.props = {"graph_name" : self.tg.name}

    def test_get_all(self):
        p_derivative = str(model.identifiers.external.derivative)
        graph = self.module.get()
        all_edges = list(graph.edges())
        actual_edges = self.tg.edge_query(e=p_derivative)
        diff = list(set(actual_edges) - set(all_edges))
        self.assertEqual(len(all_edges),len(actual_edges))
        self.assertEqual(len(diff),0)

    def test_get(self):
        node = ReservedNode("https://test_resource/BBa_test_K823003/1",
                    model.identifiers.objects.physical_entity,**self.props)
        vertex = ReservedNode("https://test_resource/BBa_test_K823004/1",**self.props)
        edge = ReservedEdge(node,vertex,model.identifiers.external.derivative,**self.props)
        self.tg.remove_edges(edge)
        self.tg.driver.submit()
        self.module.positive(node,vertex)
        res = self.module.get(node,vertex,threshold=5)
        res = list(res.edges())
        self.assertEqual([edge],res)

        self.module.negative(node,vertex)
        res = self.module.get(node,vertex,threshold=5)
        res = list(res.edges())
        self.assertEqual([],res)



    def test_positive(self):
        node = ReservedNode("https://test_resource/BBa_test_K8230036/1",
                    model.identifiers.objects.physical_entity,**self.props)
        vertex = ReservedNode("https://test_resource/BBa_test_K823005554/1",**self.props)
        edge = ReservedEdge(node,vertex,model.identifiers.external.derivative,**self.props)
        self.tg.remove_edges(edge)
        self.tg.driver.submit()
        for a in range(0,5):
            self.module.positive(node,vertex)
        res = self.module.get(node,vertex,threshold=5)
        res = list(res.edges())
        self.assertEqual([edge],res)
        self.assertEqual(res[0].confidence,25)


        for a in range(0,5):
            self.module.negative(node,vertex)
        res = self.module.get(node,vertex,threshold=5)
        res = list(res.edges())
        self.assertEqual([],res)


    def test_negative(self):
        node = ReservedNode("https://test_resource/BBa_test_K82300345/1",
                    model.identifiers.objects.physical_entity,**self.props)
        vertex = ReservedNode("https://test_resource/BBa_test_K82300456/1",**self.props)
        edge = ReservedEdge(node,vertex,model.identifiers.external.derivative,**self.props)
        self.tg.remove_edges(edge)
        self.tg.driver.submit()
        for a in range(0,5):
            self.module.positive(node,vertex)
        res = self.module.get(node,vertex,threshold=5)
        res = list(res.edges())
        self.assertEqual([edge],res)
        self.assertEqual(res[0].confidence,25)
        for a in range(0,4):
            self.module.negative(node,vertex)
        res = self.module.get(node,vertex,threshold=5)
        res = list(res.edges())
        self.assertEqual([edge],res)
        self.assertEqual(res[0].confidence,5)
        self.module.negative(node,vertex)
        res = self.module.get(node,vertex,threshold=5)
        res = list(res.edges())
        self.assertEqual([],res)

    def test_are_derivatives(self):
        d_graph = self.module.get()
        ders = list(d_graph.derivatives())
        self.assertTrue(self.module.are_derivatives(ders[0].n,ders[0].v))
        self.assertFalse(self.module.are_derivatives(ders[0].n,ders[3].v))

    def test_projection_graph_name(self):
        gn = "test_enhancer"
        fn = os.path.join("..","files","canonical_AND.xml")
        self.wg.remove_design(gn)
        convert(fn,self.tg.driver,gn)
        try:
            self.tg.project.drop("test_derivative_projection")
        except ValueError:
            pass
        res = self.tg.project.derivative("test_derivative_projection")
        pre_node_count = res.node_count()
        pre_edge_count = res.relationship_count()
        self.wg.remove_design(gn)
        self.tg.project.drop("test_derivative_projection")
        res = self.tg.project.derivative("test_derivative_projection")
        post_node_count = res.node_count()
        post_edge_count = res.relationship_count()
        self.assertEqual(pre_node_count,post_node_count)
        self.assertEqual(pre_edge_count,post_edge_count)
        ders = [e.n for e in list(self.tg.derivatives.get().derivatives())]
        for node in self.tg.procedure.degree("test_derivative_projection").keys():
            self.assertIn(node,ders)

    def test_get_components(self):
        components = self.module.get_components()
        graph = self.module.get()
        all_edges = list(graph.edges())
        all_nodes = list(graph.nodes())
        cmp_edges = []
        cmp_nodes = []
        for index,component in enumerate(components):
            for other_comp in components[index+1:]:
                self.assertFalse(any(node in other_comp for node in component.nodes()))
            self.assertTrue(nx.is_weakly_connected(component._graph))
            for edge in component.edges():
                cmp_edges.append(edge)
                cmp_nodes.append(edge.n)
                cmp_nodes.append(edge.v)
        self.assertCountEqual(all_edges,cmp_edges)
        self.assertCountEqual(all_nodes,list(set(cmp_nodes)))

nv_module = str(model.identifiers.objects.module)
nv_has_interaction = str(model.identifiers.predicates.hasInteraction)
class TestInteractionModuleModule(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.wg = WorldGraph(uri,db_auth,reserved_names=[login_graph_name])
        self.tg = self.wg.truth
        self.module = InteractionModuleModule(self.tg)
        self.props = {"graph_name" : self.tg.name}
    @classmethod
    def tearDownClass(self):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def _edge_equal(self,actual,expected):
        expected.n.properties["graph_name"] = self.tg.name
        expected.n.graph_name = self.tg.name
        expected.v.properties["graph_name"] = self.tg.name
        expected.v.graph_name = self.tg.name
        expected.properties["graph_name"] = self.tg.name
        expected.graph_name = self.tg.name
        self.assertEqual(actual,expected)
    
    def test_get(self):
        node = ReservedNode("www.test_nv/NOR/1",nv_module,**self.props)
        i_name = list(self.tg.interactions.get().nodes())[0]
        edge = ReservedEdge(node,i_name,nv_has_interaction,**self.props)
        for a in range(0,5):
            self.module.positive(node,i_name,nv_has_interaction)

        graph = self.module.get()
        modules = graph.modules()
        self.assertIn(node,modules)
        parts = graph.modules(node)
        self.assertIn(edge,parts)
        modules = graph.modules(object=i_name)
        self.assertIn(edge,modules)
        
        graph = self.module.get(node)
        modules = graph.modules()
        self.assertIn(node,modules)
        parts = graph.modules(node)
        self.assertIn(edge,parts)
        modules = graph.modules(object=i_name)
        self.assertIn(edge,modules)

        graph = self.module.get(object=i_name)
        modules = graph.modules()
        self.assertIn(node,modules)
        parts = graph.modules(node)
        self.assertIn(edge,parts)
        modules = graph.modules(object=i_name)
        self.assertIn(edge,modules)

        self.tg.remove_edges(edge)
        self.tg.driver.submit()

    def test_interaction_positive(self):
        node = ReservedNode("www.test_nv/NOR/1",nv_module,**self.props)
        i_name = list(self.tg.interactions.get().nodes())[0]
        edge = ReservedEdge(node,i_name,nv_has_interaction,**self.props)
        self.tg.remove_edges(edge)
        self.tg.driver.submit()
        for a in range(0,5):
            self.module.positive(node,i_name,nv_has_interaction)
        res = self.module.get(node,i_name,threshold=5)
        res = list(res.edges())
        self.assertEqual([edge],res)
        self.assertEqual(res[0].confidence,25)


        for a in range(0,4):
            self.module.negative(node,i_name,nv_has_interaction)
        res = self.module.get(node,i_name,threshold=5)
        res = list(res.edges())
        self.assertEqual([edge],res)
        self.assertEqual(res[0].confidence,5)
        self.module.negative(node,i_name)
        res = self.module.get(node,i_name,threshold=5)
        res = list(res.edges())
        self.assertEqual([],res)