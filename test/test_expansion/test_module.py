import sys
import os
import unittest
sys.path.insert(0, os.path.join(".."))
sys.path.insert(0, os.path.join("..",".."))
sys.path.insert(0, os.path.join("..","..",".."))
sys.path.insert(0, os.path.join("..","..","..",".."))
from app.graph.world_graph import WorldGraph
from app.graph.utility.model.model import model
from app.tools.kg_expansion.expansions.modules import TruthModules
from app.tools.data_miner.data_miner import data_miner
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

class TestModuleExpansion(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.wg = WorldGraph(uri,db_auth,reserved_names=[login_graph_name])
        self.tg = self.wg.truth
        self.module = self.tg.modules

    @classmethod
    def tearDownClass(self):
        pass
    
    def test_tg_module_enhancements(self):
        tns = TruthModules(self.tg,data_miner)
        pre_e = self.tg.edges()
        tns.expand()
        post_e = self.tg.edges()

        m_graph = self.module.get()
        i_graph = self.tg.interactions.get()
        d_graph = self.tg.derivatives.get()
        d_comps = self.tg.derivatives.get_components()
        all_parts = []
        for module in m_graph.modules():
            parts = []
            for interaction in m_graph.modules(module):
                parts += [p.v for p in i_graph.interactions(interaction=interaction.v)]
            
            for part1 in parts:
                for part2 in parts:
                        if part1 == part2:
                            continue
                        for comp in d_comps:
                            if part1 in comp and part2 in comp:
                                self.fail(f'{part1}-{part2}')
            
            for p in all_parts:
                if set(parts) == set(p):
                    self.fail(module)
            all_parts.append(parts)
        
        all_parts = [l for l in all_parts if l in d_graph]
        for index1,p_group1 in enumerate(all_parts):
            for index2,p_group2 in enumerate(all_parts):
                if index1 == index2:
                    continue
                for pg1 in p_group1:
                    for pg2 in p_group2:
                        for comp in d_comps:
                            if pg1 in comp and pg2 in comp:
                                break
                    else:
                        self.fail(pg1)

        pre_e = self.tg.edges()
        tns.expand()
        post_e = self.tg.edges()
        self.assertEqual(len(list(set(post_e) - set(pre_e))),0)