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
from app.tools.kg_expansion.expansions.text_extraction import TruthTextExtraction
from app.tools.data_miner.data_miner import data_miner
from app.graph.utility.graph_objects.reserved_node import ReservedNode
from app.tools.aligner import aligner
curr_dir = os.path.dirname(os.path.realpath(__file__))
db_host = os.environ.get('NEO4J_HOST', 'localhost')
db_port = os.environ.get('NEO4J_PORT', '7687')
db_auth = os.environ.get('NEO4J_AUTH', "neo4j/Radeon12300")
db_auth = tuple(db_auth.split("/"))
uri = f'neo4j://{db_host}:{db_port}'
login_graph_name = "login_manager"

nv_synonym = model.identifiers.external.synonym
nv_derivatives = model.identifiers.external.derivative
nv_promoter = model.identifiers.objects.promoter
nv_seq = model.identifiers.predicates.hasSequence
class TestIdentifyDerivative(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.wg = WorldGraph(uri,db_auth,reserved_names=[login_graph_name])
        self.tg = self.wg.truth


    @classmethod
    def tearDownClass(self):
        pass
    
    def test_text_extraction_expansion(self):
        ppe = TruthTextExtraction(self.tg,data_miner)
        pre_e = self.tg.edges()
        ppe.expand()
        post_e = self.tg.edges()



    