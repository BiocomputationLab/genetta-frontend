import sys
import os
import unittest

sys.path.insert(0, os.path.join(".."))
sys.path.insert(0, os.path.join("..",".."))
sys.path.insert(0, os.path.join("..","..",".."))
sys.path.insert(0, os.path.join("..","..","..",".."))
sys.path.insert(0, os.path.join("..","..","..","..",".."))
from app.graph.world_graph import WorldGraph
from app.converter.sbol_convert import convert
curr_dir = os.path.dirname(os.path.realpath(__file__))

db_host = os.environ.get('NEO4J_HOST', 'localhost')
db_port = os.environ.get('NEO4J_PORT', '7687')
db_auth = os.environ.get('NEO4J_AUTH', "neo4j/Radeon12300")
db_auth = tuple(db_auth.split("/"))
uri = f'neo4j://{db_host}:{db_port}'
login_graph_name = "login_manager"

fn = os.path.join(curr_dir,"..","..","files","nor_full.xml")
class TestDesignGraph(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.gn = "test_dg"
        self.wg = WorldGraph(uri,db_auth)
        convert(fn,self.wg.driver,self.gn)
        self.dg = self.wg.get_design(self.gn)

    @classmethod
    def tearDownClass(self):
        self.wg.remove_design(self.gn)

    def test_drop(self):
        self.wg.remove_design(self.gn)
        dg = self.wg.get_design(self.gn)
        self.assertEqual(dg.nodes(),[])
        self.assertEqual(dg.edges(),[])
        convert(fn,self.wg.driver,self.gn)
        

    def test_get_children(self):
        pes = self.dg.get_physicalentity()
        for entity in pes:
            for edge in self.dg.get_children(entity):
                self.assertIn(edge.v,pes)
                self.assertEqual(edge.n,entity)

    def test_get_parents(self):
        pes = self.dg.get_physicalentity()
        for entity in pes:
            for edge in self.dg.get_parents(entity):
                self.assertIn(edge.n,pes)
                self.assertEqual(edge.v,entity)


        
        


