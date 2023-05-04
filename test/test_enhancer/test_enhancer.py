import sys
import os
import unittest

sys.path.insert(0, os.path.join(".."))
sys.path.insert(0, os.path.join("..",".."))
sys.path.insert(0, os.path.join("..","..",".."))
sys.path.insert(0, os.path.join("..","..","..",".."))
from app.graph.world_graph import WorldGraph
from app.tools.enhancer.enhancer import Enhancer
curr_dir = os.path.dirname(os.path.realpath(__file__))
fn = os.path.join("test","files","nor_full.xml")

db_host = os.environ.get('NEO4J_HOST', 'localhost')
db_port = os.environ.get('NEO4J_PORT', '7687')
db_auth = os.environ.get('NEO4J_AUTH', "neo4j/Radeon12300")
db_auth = tuple(db_auth.split("/"))
uri = f'neo4j://{db_host}:{db_port}'
login_graph_name = "login_manager"

class TestEnhancer(unittest.TestCase):
    
    @classmethod
    def setUpClass(self):
        self.gn = "test_enhancer"
        self.wg = WorldGraph(uri,db_auth,reserved_names=[login_graph_name])
        self.enhancer = Enhancer(self.wg)
        self.miner = self.enhancer._miner

    @classmethod
    def tearDownClass(self):
        self.wg.remove_design(self.gn)
    
    # --- Truth ---
    def test_expand_truth_graph(self):
        self.enhancer.expand_truth_graph()

    def test_apply_truth_graph(self):
        pass
 
    def test_apply_truth_graph(self):
        pass


        





