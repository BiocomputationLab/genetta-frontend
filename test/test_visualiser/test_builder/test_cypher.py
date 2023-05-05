import unittest
import os
import sys

sys.path.insert(0, os.path.join(".."))
sys.path.insert(0, os.path.join("..",".."))
sys.path.insert(0, os.path.join("..","..",".."))
from app.converter.sbol_convert import convert
from app.tools.visualiser.builder.cypher import CypherBuilder
from app.graph.world_graph import WorldGraph

curr_dir = os.path.dirname(os.path.realpath(__file__))
db_host = os.environ.get('NEO4J_HOST', 'localhost')
db_port = os.environ.get('NEO4J_PORT', '7687')
db_auth = os.environ.get('NEO4J_AUTH', "neo4j/Radeon12300")
db_auth = tuple(db_auth.split("/"))
uri = f'neo4j://{db_host}:{db_port}'
login_graph_name = "login_manager"

class TestViews(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.gn = "test_builder_views"
        self.wg = WorldGraph(uri,db_auth)
        self.builder = CypherBuilder(self.wg)

    @classmethod
    def tearDownClass(self):
        pass
    
    def test_cypher(self):
        gn = "test_cypher"
        fn = os.path.join(curr_dir,"..","..","files","nor_full.xml")
        self.wg.remove_design(gn)
        convert(fn,self.wg.driver,gn)
        cypher_qry = "match (n) return n Limit 25"
        self.builder.set_cypher_view()
        self.builder.set_query(cypher_qry)
        dt = self.builder.build(True)
        graph = self.builder.view
        self.assertTrue(len(list(graph.nodes())) <= 25)
        self.assertTrue(len(dt) == 25)
        self.wg.remove_design(gn)

if __name__ == '__main__':
    unittest.main()
