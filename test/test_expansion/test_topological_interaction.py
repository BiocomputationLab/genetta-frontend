import sys
import os
import unittest
from rdflib import URIRef
sys.path.insert(0, os.path.join(".."))
sys.path.insert(0, os.path.join("..",".."))
sys.path.insert(0, os.path.join("..","..",".."))
sys.path.insert(0, os.path.join("..","..","..",".."))
from app.graph.world_graph import WorldGraph
from app.graph.utility.model.model import model
from app.tools.kg_expansion.expansions.topological_interaction import TruthTopologicalInteraction
from app.tools.data_miner.data_miner import data_miner
curr_dir = os.path.dirname(os.path.realpath(__file__))
db_host = os.environ.get('NEO4J_HOST', 'localhost')
db_port = os.environ.get('NEO4J_PORT', '7687')
db_auth = os.environ.get('NEO4J_AUTH', "neo4j/Radeon12300")
db_auth = tuple(db_auth.split("/"))
uri = f'neo4j://{db_host}:{db_port}'
login_graph_name = "login_manager"

class TestTruthTopologicalInteraction(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.wg = WorldGraph(uri,db_auth,reserved_names=[login_graph_name])
        self.tg = self.wg.truth


    @classmethod
    def tearDownClass(self):
        pass
    
    def test_identify_derivative_expansion(self):
        tie = TruthTopologicalInteraction(self.tg,data_miner)
        tie.expand()

    