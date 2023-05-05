import sys
import os
import unittest
sys.path.insert(0, os.path.join(".."))
sys.path.insert(0, os.path.join("..",".."))
sys.path.insert(0, os.path.join("..","..",".."))
sys.path.insert(0, os.path.join("..","..","..",".."))
from app.graph.world_graph import WorldGraph
from app.tools.enhancer.enhancer import Enhancer
from app.graph.utility.model.model import model
from app.graph.truth_graph.modules.interaction import InteractionModule
from app.tools.enhancer.enhancements.interaction.derivative import TruthDerivative
curr_dir = os.path.dirname(os.path.realpath(__file__))

db_host = os.environ.get('NEO4J_HOST', 'localhost')
db_port = os.environ.get('NEO4J_PORT', '7687')
db_auth = os.environ.get('NEO4J_AUTH', "neo4j/Radeon12300")
db_auth = tuple(db_auth.split("/"))
uri = f'neo4j://{db_host}:{db_port}'
login_graph_name = "login_manager"


nv_p = str(model.identifiers.objects.protein)
nv_pp = str(model.identifiers.objects.genetic_production)
nv_cds = str(model.identifiers.objects.cds)
nv_template = str(model.identifiers.predicates.template)
nv_product = str(model.identifiers.predicates.product)

class TestDerivativeExpansion(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.wg = WorldGraph(uri,db_auth,reserved_names=[login_graph_name])
        self.tg = self.wg.truth
        self.enhancer = Enhancer(self.wg)
        self.im = InteractionModule(self.wg.truth)

    @classmethod
    def tearDownClass(self):
        pass
    
    def test_tg_derivative_enhancements(self):
        ppe = TruthDerivative(self.wg,self.enhancer._miner)
        pre_e = self.tg.edges()
        ppe.enhance()
        post_e = self.tg.edges()
        diff = list(set(post_e) - set(pre_e))
        g_graph = self.tg.derivatives.get()
        i_graph = self.tg.interactions.get()
        seens = []
        for i in i_graph.interactions():
            i_eles = set([i.get_type()] + 
                         [i.v for i in i_graph.interaction_elements(i)])
            self.assertNotIn(i_eles,seens)
            seens.append(i_eles)

        for d in g_graph.derivatives():
            d = d.n
            d_is = []
            for i in i_graph.interactions(entity=d):
                d_is.append(set([i.get_type()] + 
                                [i.v for i in i_graph.interaction_elements(i)  if i.v != d]))
            for dd in g_graph.derivatives(d):
                dd = dd.v
                dd_is = []
                for dd_i in i_graph.interactions(entity=dd):
                    dd_is.append(set([dd_i.get_type()] + 
                                     [i.v for i in i_graph.interaction_elements(dd_i) if i.v != dd]))
            self.assertCountEqual(d_is,dd_is)

        pre_e = self.tg.edges()
        ppe.enhance()
        post_e = self.tg.edges()
        diff = list(set(post_e) - set(pre_e))
        self.assertEqual(len(diff),0)