import sys
import os
import unittest

sys.path.insert(0, os.path.join(".."))
sys.path.insert(0, os.path.join("..",".."))
sys.path.insert(0, os.path.join("..","..",".."))
sys.path.insert(0, os.path.join("..","..","..",".."))
from app.graph.world_graph import WorldGraph
from app.tools.enhancer.enhancer import Enhancer
from app.tools.enhancer.enhancements.tg_interactions import TruthInteractions
from app.tools.enhancer.enhancements.positional import Positional
from app.tools.enhancer.enhancements.protein_production import ProteinProduction
from app.tools.enhancer.enhancements.protein_production import defered_int_types
from app.tools.enhancer.enhancements.text_extraction import TextExtraction
from app.converter.sbol_convert import convert
from app.graph.utility.model.model import model

curr_dir = os.path.dirname(os.path.realpath(__file__))
fn = os.path.join("test","files","canonical_AND.xml")

db_host = os.environ.get('NEO4J_HOST', 'localhost')
db_port = os.environ.get('NEO4J_PORT', '7687')
db_auth = os.environ.get('NEO4J_AUTH', "neo4j/Radeon12300")
db_auth = tuple(db_auth.split("/"))
uri = f'neo4j://{db_host}:{db_port}'
login_graph_name = "login_manager"

nv_promoter = str(model.identifiers.objects.promoter)
nv_cds = str(model.identifiers.objects.cds)
nv_pp = str(model.identifiers.objects.genetic_production)
nv_activation = str(model.identifiers.objects.activation)
nv_activator = str(model.identifiers.predicates.activator)
nv_activated = str(model.identifiers.predicates.activated)

class TestEnhancer(unittest.TestCase):
    
    @classmethod
    def setUpClass(self):
        self.gn = "test_enhancer"
        self.wg = WorldGraph(uri,db_auth,reserved_names=[login_graph_name])
        self.enhancer = Enhancer(self.wg)
        self.miner = self.enhancer._miner
        self.wg.remove_design(self.gn)
        convert(fn,self.wg.driver,self.gn)
        

    def tearDown(self):
        pass#self.wg.remove_design(self.gn)


    def test_enhance_protein_production_manual_AND(self):
        enhancer = ProteinProduction(self.wg,self.miner)
        changes = enhancer.enhance(self.gn,automated=False)
        graph = self.wg.get_design(self.gn)
        cds = [k.get_key() for k in graph.get_cds()]
        replacements = {}
        for k,v in changes.items():
            self.assertIn(k,cds)
            replacements[k] = list(v.keys())[0]
        enhancer.apply(replacements,self.gn)
        for cd in cds:
            cd_ints = graph.get_interactions(cd)
            for cdi in cd_ints:
                if cdi.n.get_type() == nv_pp:
                    break
            else:
                self.fail()

    def test_enhance_protein_production_automated_AND(self):
        enhancer = ProteinProduction(self.wg,self.miner)
        enhancer.enhance(self.gn,automated=True)
        graph = self.wg.get_design(self.gn)
        cds = graph.get_cds()
        for cd in cds:
            cd_ints = graph.get_interactions(cd)
            for cdi in cd_ints:
                if cdi.n.get_type() == nv_pp:
                    break
            else:
                self.fail()

    def test_enhance_protein_production_manual_existing_interactions(self):
        t_fn = os.path.join("test","files","protein_production_existing_interactions.xml")
        gn = "test_enhance_protein_production_existing_interactions"
        self.wg.remove_design(gn)
        convert(t_fn,self.wg.driver,gn)
        enhancer = ProteinProduction(self.wg,self.miner)
        changes = enhancer.enhance(gn,automated=False)
        graph = self.wg.get_design(gn)
        cds = [k.get_key() for k in graph.get_cds()]
        replacements = {}
        for k,v in changes.items():
            val = list(v.keys())[0]
            replacements[k] = val
        enhancer.apply(replacements,gn)
        for cd in cds:
            cd_ints = [i.n.get_type() for i in graph.get_interactions(cd)]
            self.assertIn(nv_pp,cd_ints)
            for def_int in defered_int_types:
                self.assertNotIn(def_int,cd_ints)
        self.wg.remove_design(gn)

    def test_enhance_protein_production_automated_existing_interactions(self):
        t_fn = os.path.join("test","files","protein_production_existing_interactions.xml")
        gn = "test_enhance_protein_production_existing_interactions"
        self.wg.remove_design(gn)
        convert(t_fn,self.wg.driver,gn)
        enhancer = ProteinProduction(self.wg,self.miner)
        changes = enhancer.enhance(gn,automated=True)
        graph = self.wg.get_design(gn)
        cds = graph.get_cds()
        for cd in cds:
            cd_ints = graph.get_interactions(cd)
            for cdi in cd_ints:
                if cdi.n.get_type() == nv_pp:
                    break
            else:
                self.fail()
        self.wg.remove_design(gn)


    def test_enhance_interactions_manual_AND(self):
        enhancer = TruthInteractions(self.wg,self.miner)
        changes = enhancer.enhance(self.gn,automated=False)
        graph = self.wg.get_design(self.gn)
        pre_d_ints = graph.get_interactions()
        pes = [k.get_key() for k in graph.get_physicalentity()]
        t_ints = self.wg.truth.interactions.get()
        replacements = {}
        for k,v in changes.items():
            self.assertIn(k,pes)
            interaction = [k.get_key() for k in 
                           t_ints.interactions(participant=k)]
            self.assertIn(list(v.keys())[0],interaction)
            replacements[k] = list(v.keys())[0]

        enhancer.apply(replacements,self.gn)
        post_d_ints = graph.get_interactions()
        diff = list(set(post_d_ints) - set(pre_d_ints))
        for d in diff:
            d_int = list(t_ints.interactions(d.n.get_key()))
            self.assertTrue(d.is_in(d_int))
        post_t_ints = self.wg.truth.interactions.get()
        self.assertEqual(t_ints,post_t_ints)

    def test_enhance_interactions_automated_AND(self):
        enhancer = TruthInteractions(self.wg,self.miner)
        graph = self.wg.get_design(self.gn)
        pre_d_ints = graph.get_interactions()
        enhancer.enhance(self.gn,automated=True)

        t_ints = self.wg.truth.interactions.get()
        post_d_ints = graph.get_interactions()
        diff = list(set(post_d_ints) - set(pre_d_ints))
        for d in diff:
            d_int = list(t_ints.interactions(d.n.get_key()))
            self.assertTrue(d.is_in(d_int))
        post_t_ints = self.wg.truth.interactions.get()
        self.assertEqual(t_ints,post_t_ints)

    def test_enhance_tg_interaction_existing_interactions(self):
        t_fn = os.path.join("test","files","AND_canonical_partial_ints.xml")
        gn = "test_enhance_AND_canonical_partial_ints"
        self.wg.remove_design(gn)
        convert(t_fn,self.wg.driver,gn)
        graph = self.wg.get_design(gn)
        pes = [k.get_key() for k in graph.get_physicalentity()]
        enhancer = TruthInteractions(self.wg,self.miner)
        enhancer.enhance(gn,automated=True)
        
        for e in pes:
            ints = graph.get_interactions(e)
            if len(ints) == 0:
                continue
            i_counts = []
            for i in ints:
                if i.get_type() in i_counts:
                    self.fail(i)
                i_counts.append(i.get_type())
        self.wg.remove_design(gn)


    def test_enhance_positional_manual_AND(self):
        enhancer = Positional(self.wg,self.miner)
        changes = enhancer.enhance(self.gn,automated=False)


        graph = self.wg.get_design(self.gn)
        pre_d_ints = graph.get_interactions()
        pes = [k.get_key() for k in graph.get_physicalentity()]
        replacements = {}
        for k,v in changes.items():
            self.assertIn(k,pes)
            self.assertIn(list(v.keys())[0],pes)
            replacements[k] = list(v.keys())[0]

        enhancer.apply(replacements,self.gn)
        post_d_ints = graph.get_interactions()
        diff = list(set(post_d_ints) - set(pre_d_ints))
        positional_pes_type = [nv_promoter,nv_cds]
        positional_part_type = [nv_activator,nv_activated]
        for d in diff:
            self.assertEqual(d.n.get_type(),nv_activation)
            self.assertIn(d.v.get_type(),positional_pes_type)
            self.assertIn(d.get_type(),positional_part_type)

    def test_enhance_positional_automated_AND(self):
        enhancer = Positional(self.wg,self.miner)
        graph = self.wg.get_design(self.gn)
        pre_d_ints = graph.get_interactions()
        changes = enhancer.enhance(self.gn,automated=True)
        post_d_ints = graph.get_interactions()
        diff = list(set(post_d_ints) - set(pre_d_ints))
        positional_pes_type = [nv_promoter,nv_cds]
        positional_part_type = [nv_activator,nv_activated]
        for d in diff:
            self.assertEqual(d.n.get_type(),nv_activation)
            self.assertIn(d.v.get_type(),positional_pes_type)
            self.assertIn(d.get_type(),positional_part_type)

    def test_enhance_positional_existing(self):
        t_fn = os.path.join("test","files","canonical_AND_act_ints.xml")
        gn = "test_enhance_positional_existing"
        self.wg.remove_design(gn)
        convert(t_fn,self.wg.driver,gn)
        graph = self.wg.get_design(gn)

        enhancer = Positional(self.wg,self.miner)
        graph = self.wg.get_design(gn)
        pre_d_ints = graph.get_interactions()
        changes = enhancer.enhance(gn,automated=True)
        post_d_ints = graph.get_interactions()
        diff = list(set(post_d_ints) - set(pre_d_ints))
        self.assertEqual(len(diff),0)

        self.wg.remove_design(gn)

    def test_enhance_positional_existing2(self):
        t_fn = os.path.join("test","files","nor_full.xml")
        gn = "test_enhance_positional_existing2"
        self.wg.remove_design(gn)
        convert(t_fn,self.wg.driver,gn)
        graph = self.wg.get_design(gn)

        enhancer = Positional(self.wg,self.miner)
        graph = self.wg.get_design(gn)
        pre_d_ints = graph.get_interactions()
        changes = enhancer.enhance(gn,automated=True)
        post_d_ints = graph.get_interactions()
        diff = list(set(post_d_ints) - set(pre_d_ints))
        self.assertEqual(len(diff),0)

        self.wg.remove_design(gn)

    def test_enhance_positional_multi_graph(self):
        t_fn1 = os.path.join("test","files","canonical_AND_act_ints.xml")
        gn1 = "test_enhance_positional_existing1"
        self.wg.remove_design(gn1)
        convert(t_fn1,self.wg.driver,gn1)

        t_fn1 = os.path.join("test","files","nor_full.xml")
        gn2 = "test_enhance_positional_existing2"
        self.wg.remove_design(gn2)
        convert(t_fn1,self.wg.driver,gn2)

        enhancer = Positional(self.wg,self.miner)
        changes = enhancer.enhance(self.gn,automated=False)

        graph = self.wg.get_design(self.gn)
        pre_d_ints = graph.get_interactions()
        pes = [k.get_key() for k in graph.get_physicalentity()]
        replacements = {}
        for k,v in changes.items():
            self.assertIn(k,pes)
            self.assertIn(list(v.keys())[0],pes)
            replacements[k] = list(v.keys())[0]

        enhancer.apply(replacements,self.gn)
        post_d_ints = graph.get_interactions()
        diff = list(set(post_d_ints) - set(pre_d_ints))
        positional_pes_type = [nv_promoter,nv_cds]
        positional_part_type = [nv_activator,nv_activated]
        for d in diff:
            self.assertEqual(d.n.get_type(),nv_activation)
            self.assertIn(d.v.get_type(),positional_pes_type)
            self.assertIn(d.get_type(),positional_part_type)

        self.wg.remove_design(gn1)
        self.wg.remove_design(gn2)

    def test_enhance_positional_multi_component(self):
        t_fn1 = os.path.join("test","files","nor_full.xml")
        gn2 = "test_enhance_positional_multi_component"
        self.wg.remove_design(gn2)
        convert(t_fn1,self.wg.driver,gn2)

        enhancer = Positional(self.wg,self.miner)
        changes = enhancer.enhance([self.gn,gn2],automated=False)

        graph = self.wg.get_design([self.gn,gn2])
        pre_d_ints = graph.get_interactions()
        pes = [k.get_key() for k in graph.get_physicalentity(predicate="ANY")]
        replacements = {}
        for k,v in changes.items():
            self.assertIn(k,pes)
            self.assertIn(list(v.keys())[0],pes)
            replacements[k] = list(v.keys())

        enhancer.apply(replacements,[self.gn,gn2])
        post_d_ints = graph.get_interactions()
        diff = list(set(post_d_ints) - set(pre_d_ints))
        positional_pes_type = [nv_promoter,nv_cds]
        positional_part_type = [nv_activator,nv_activated]
        for d in diff:
            self.assertEqual(d.n.get_type(),nv_activation)
            self.assertIn(d.v.get_type(),positional_pes_type)
            self.assertIn(d.get_type(),positional_part_type)
        self.wg.remove_design(gn2)




    def test_enhance_text_extraction_manual_AND(self):
        enhancer = TextExtraction(self.wg,self.miner)
        enhancer.enhance(self.gn,automated=False)

    def test_enhance_text_extraction_automated_AND(self):
        enhancer = TextExtraction(self.wg,self.miner)
        enhancer.enhance(self.gn,automated=False)



    def test_enhance_automated(self):
        self.enhancer.enhance(self.gn,automated=False)

    def test_enhance_manual(self):
        self.enhancer.enhance(self.gn,automated=False)
        





