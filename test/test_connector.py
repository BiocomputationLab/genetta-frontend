import sys
import os
import unittest
import re
sys.path.insert(0, os.path.join(".."))
sys.path.insert(0, os.path.join("..",".."))
sys.path.insert(0, os.path.join("..","..",".."))
sys.path.insert(0, os.path.join("..","..","..",".."))
from app.converter.sbol_convert import convert as sb_convert 
from app.graph.world_graph import WorldGraph
from app.converter.utility.graph import SBOLGraph
curr_dir = os.path.dirname(os.path.realpath(__file__))

db_host = os.environ.get('NEO4J_HOST', 'localhost')
db_port = os.environ.get('NEO4J_PORT', '7687')
db_auth = os.environ.get('NEO4J_AUTH', "neo4j/Radeon12300")
db_auth = tuple(db_auth.split("/"))
uri = f'neo4j://{db_host}:{db_port}'
login_graph_name = "login_manager"
curr_dir = os.path.dirname(os.path.realpath(__file__))

from app.utility.sbol_connector.connector import SBOLConnector

class TestConnector(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.connector = SBOLConnector()

    @classmethod
    def tearDownClass(self):
        pass
    
    def test_connector_split_collection(self):
        graph = WorldGraph(uri,db_auth,reserved_names=[login_graph_name])
        fn = os.path.join("files","iGEM_2016_interlab_collection_connected.xml")
        gn = "test_connector"
        res = self.connector.split(fn,gn)
        for path,gn in res:
            graph.remove_design(gn)
            sb_convert(path,graph.driver,gn)
            dg = graph.get_design(gn)
            pes = dg.get_physicalentity()
            root = pes.pop(0)
            for e in dg.get_haspart(root):
                self.assertEqual(root,e.n)
                self.assertIn(e.v,pes)
            dg.drop()
            os.remove(path)


def get_name(subject):
    split_subject = split(subject)
    if len(split_subject[-1]) == 1 and split_subject[-1].isdigit():
        return split_subject[-2]
    else:
        return split_subject[-1]

def split(uri):
    return re.split('#|\/|:', uri)