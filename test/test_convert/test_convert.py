import sys
import os
import unittest

sys.path.insert(0, os.path.join(".."))
sys.path.insert(0, os.path.join("..",".."))
sys.path.insert(0, os.path.join("..","..",".."))
sys.path.insert(0, os.path.join("..","..","..",".."))
sys.path.insert(0, os.path.join("..","..","..","..",".."))
from app.converter.sbol_convert import convert as sb_convert 
from app.converter.gbk_convert import convert as gb_convert 
from app.graph.world_graph import WorldGraph
from app.converter.utility.graph import SBOLGraph
curr_dir = os.path.dirname(os.path.realpath(__file__))

db_host = os.environ.get('NEO4J_HOST', 'localhost')
db_port = os.environ.get('NEO4J_PORT', '7687')
db_auth = os.environ.get('NEO4J_AUTH', "neo4j/Radeon12300")
db_auth = tuple(db_auth.split("/"))
uri = f'neo4j://{db_host}:{db_port}'
login_graph_name = "login_manager"

class TestConvert(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    
    def test_sbol(self):
        fn = os.path.join("..","files","nor_full.xml")
        sbol_graph = SBOLGraph(fn)
        gn = "test_sbol"
        graph = WorldGraph(uri,db_auth,reserved_names=[login_graph_name])
        sb_convert(fn,graph.driver,gn)
        dg = graph.get_design(gn)

        s_cds = [str(s) for s in sbol_graph.get_component_definitions()]
        pes = [p.get_key() for p in dg.get_physicalentity()]
        self.assertCountEqual(pes,s_cds)

        s_i = [str(s) for s in sbol_graph.get_interactions()]
        ints = [p.get_key() for p in dg.get_interaction()]
        self.assertCountEqual(ints,s_i)

        dg.drop()

    def test_sbol2(self):
        fn = os.path.join("..","files","interaction.xml")
        sbol_graph = SBOLGraph(fn)
        gn = "interaction"
        graph = WorldGraph(uri,db_auth,reserved_names=[login_graph_name])
        sb_convert(fn,graph.driver,gn)
        dg = graph.get_design(gn)

        s_cds = [str(s) for s in sbol_graph.get_component_definitions()]
        pes = [p.get_key() for p in dg.get_physicalentity()]
        self.assertCountEqual(pes,s_cds)

        s_i = [str(s) for s in sbol_graph.get_interactions()]
        ints = [p.get_key() for p in dg.get_interaction()]
        self.assertCountEqual(ints,s_i)
        dg.drop()

    def test_sbol_sequence(self):
        fn1 = os.path.join("..","files","convert_sequence.xml")
        sg1 = SBOLGraph(fn1)
        gn1 = "sb1"
        graph = WorldGraph(uri,db_auth,reserved_names=[login_graph_name])
        sb_convert(fn1,graph.driver,gn1)
        dg1 = graph.get_design([gn1])
        s_cds = sg1.get_component_definitions()
        for pe in dg1.get_physicalentity():
            for cd in s_cds:
                if str(cd) == str(pe.get_key()):
                    if len(sg1.get_sequence_names(cd)) > 0:
                        self.assertTrue(hasattr(pe,"hasSequence"))
                    break
            else:
                self.fail()
        dg1.drop()

    def test_sbol_overlap(self):
        fn1 = os.path.join("..","files","sbol_overlap1.xml")
        fn2 = os.path.join("..","files","sbol_overlap2.xml")
        sg1 = SBOLGraph(fn1)
        sg2 = SBOLGraph(fn2)
        gn1 = "sb1"
        gn2 = "sb2"
        graph = WorldGraph(uri,db_auth,reserved_names=[login_graph_name])
        sb_convert(fn1,graph.driver,gn1)
        sb_convert(fn2,graph.driver,gn2)
        dg1 = graph.get_design([gn1])
        dg2 = graph.get_design([gn2])
        c_g = sg1 + sg2
        pes = list(set([str(s) for s in dg2.get_physicalentity()] + [str(s) for s in dg1.get_physicalentity()]))
        s_cds = [str(s) for s in c_g.get_component_definitions()]
        self.assertCountEqual(pes,s_cds)
        dg1.drop()
        dg2.drop()
    
    def test_gbk(self):
        fn = os.path.join("..","files","nor_reporter.gb")
        gn = "test_gbk"
        graph = WorldGraph(uri,db_auth,reserved_names=[login_graph_name])
        gb_convert(fn,graph.driver,gn)
        dg = graph.get_design(gn)
        pes = dg.get_physicalentity()
        root = pes.pop(0)
        for e in dg.get_haspart(root):
            self.assertEqual(root,e.n)
            self.assertIn(e.v,pes)
        dg.drop()

    def test_gbk2(self):
        fn = os.path.join("..","files","0xF6.gbk")
        gn = "test_gbk"
        graph = WorldGraph(uri,db_auth,reserved_names=[login_graph_name])
        graph.remove_design(gn)
        gb_convert(fn,graph.driver,gn)
        dg = graph.get_design(gn)
        pes = dg.get_physicalentity()
        root = pes.pop(0)
        for e in dg.get_haspart(root):
            self.assertEqual(root,e.n)
            self.assertIn(e.v,pes)
        dg.drop()

    def test_sbol_positional_relative(self):
        fn = os.path.join("..","files","canonical_AND.xml")
        sbol_graph = SBOLGraph(fn)
        gn = "test_sbol_positional_relative"
        graph = WorldGraph(uri,db_auth,reserved_names=[login_graph_name])
        sb_convert(fn,graph.driver,gn)
        dg = graph.get_design(gn)
        

        s_cds = [str(s) for s in sbol_graph.get_component_definitions()]
        pes = [p.get_key() for p in dg.get_physicalentity()]
        self.assertCountEqual(pes,s_cds)

        s_i = [str(s) for s in sbol_graph.get_interactions()]
        ints = [p.get_key() for p in dg.get_interaction()]
        self.assertCountEqual(ints,s_i)

        positions = dg.get_position()
        seen_pos = []
        for p in positions:
            po = dg.get_positionof(p)
            nex = dg.get_next(p)
            self.assertEqual(len(po),1)
            po = po[0]
            self.assertNotIn(po.v,seen_pos)
            seen_pos.append(po.v)
            if len(nex) > 0:
                self.assertEqual(len(nex),1)
                nex = nex[0]
                self.assertEqual(nex.n.get_type(),nex.v.get_type())
            else:
                self.assertEqual(len(nex),0)

    def test_sbol_absolute(self):
        fn = os.path.join("..","files","0xF6.xml")
        sbol_graph = SBOLGraph(fn)
        gn = "test_sbol_absolute"
        graph = WorldGraph(uri,db_auth,reserved_names=[login_graph_name])
        sb_convert(fn,graph.driver,gn)
        dg = graph.get_design(gn)
        

        s_cds = [str(s) for s in sbol_graph.get_component_definitions()]
        pes = [p.get_key() for p in dg.get_physicalentity()]
        self.assertCountEqual(pes,s_cds)

        s_i = [str(s) for s in sbol_graph.get_interactions()]
        ints = [p.get_key() for p in dg.get_interaction()]
        self.assertCountEqual(ints,s_i)

        positions = dg.get_position()
        seen_pos = []
        for p in positions:
            po = dg.get_positionof(p)
            nex = dg.get_next(p)
            self.assertEqual(len(po),1)
            po = po[0]
            self.assertNotIn(po.v,seen_pos)
            seen_pos.append(po.v)
            if len(nex) > 0:
                self.assertEqual(len(nex),1)
                nex = nex[0]
                self.assertEqual(nex.n.get_type(),nex.v.get_type())
            else:
                self.assertEqual(len(nex),0)

    def test_sbol_collection(self):
        fn = os.path.join("..","files","iGEM_2016_interlab_collection_connected.xml")
        gn = "test_sbol_collection"
        graph = WorldGraph(uri,db_auth,reserved_names=[login_graph_name])
        graph.remove_design(gn)
        sb_convert(fn,graph.driver,gn)
        dg = graph.get_design(gn)
        pes = dg.get_physicalentity()
        root = pes.pop(0)
        for e in dg.get_haspart(root):
            self.assertEqual(root,e.n)
            self.assertIn(e.v,pes)
        dg.drop()

    def test_interlab(self):
        fn = os.path.join("..","files","Negative_2016Interlab.xml")
        gn = "test_sbol_collection"
        graph = WorldGraph(uri,db_auth,reserved_names=[login_graph_name])
        graph.remove_design(gn)
        sb_convert(fn,graph.driver,gn)
        dg = graph.get_design(gn)
        pes = dg.get_physicalentity()
        root = pes.pop(0)
        for e in dg.get_haspart(root):
            self.assertEqual(root,e.n)
            self.assertIn(e.v,pes)
        dg.drop()
