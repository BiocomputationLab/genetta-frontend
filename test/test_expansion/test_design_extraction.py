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
from app.tools.kg_expansion.expansions.design_extraction import TruthDesignExtraction
from app.tools.data_miner.data_miner import data_miner
from app.converter.handler import file_convert
from app.converter.utility.graph import SBOLGraph

curr_dir = os.path.dirname(os.path.realpath(__file__))

db_host = os.environ.get('NEO4J_HOST', 'localhost')
db_port = os.environ.get('NEO4J_PORT', '7687')
db_auth = os.environ.get('NEO4J_AUTH', "neo4j/Radeon12300")
db_auth = tuple(db_auth.split("/"))
uri = f'neo4j://{db_host}:{db_port}'
login_graph_name = "login_manager"

nv_cds = str(model.identifiers.objects.cds)
nv_template = str(model.identifiers.predicates.template)
nv_syn = str(model.identifiers.external.synonym)
nv_has_sequence = model.identifiers.predicates.has_sequence
nv_promoter = str(model.identifiers.objects.promoter)
nv_dna = str(model.identifiers.objects.dna)
nv_activation = str(model.identifiers.objects.activation)

class TestDesignExtraction(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.wg = WorldGraph(uri,db_auth,reserved_names=[login_graph_name])
        self.tg = self.wg.truth
        self.ppe = TruthDesignExtraction(self.wg,data_miner)
        self.diff_edges = []
        self.delete_graphs = []

    @classmethod
    def tearDownClass(self):
        for d in self.diff_edges:
            self.tg.interactions.negative(d.n,d.v,d.get_type())
        for d in self.delete_graphs:
            self.wg.remove_design(d)

    
    def test_design_extraction_expansion(self):
        designs = [os.path.join("files","0x87.xml")]
        for d in designs:
            d_n = d.split(os.path.sep)[-1].split(".")[0]
            file_convert(self.wg.driver, d,d_n)
        self.delete_graphs.append(d_n)
        pre_e = self.tg.edges()
        self.ppe.integrate_design(d_n)
        post_e = self.tg.edges()

        diff = list(set(post_e) - set(pre_e))
        self.diff_edges += diff

        syns = [s.v for s in self.tg.synonyms.get().synonyms()]
        self.assertEqual(len(syns),len(list(set(syns))))

    def test_integrate_design_design_specific_interactions(self):
        fn = os.path.join("files","test_integrate_design_design_specific_interactions.xml")
        d_n = "test_integrate_design_design_specific_interactions"
        self.wg.remove_design(d_n)
        if d_n not in self.wg.get_design_names():
            file_convert(self.wg.driver, fn,d_n)
        self.delete_graphs.append(d_n)

        design = self.wg.get_design(d_n)
        d_i  = design.get_interactions()
        self.ppe.integrate_design(d_n)
        post_e = [i.n.get_key() for i in self.tg.edges()]
        for i in d_i:
            eles = [e.v.get_type() for e in 
                    design.get_interaction_elements(i.n)]
            if i.n.get_type() == nv_activation:
                if nv_dna in eles and nv_promoter in eles:
                    self.assertNotIn(i.n.get_key(),post_e)


    def test_integrate_design_direct_uri(self):
        fn = os.path.join("files","test_integrate_design_direct_uri.xml")
        d_n = "test_integrate_design_direct_uri"
        self.wg.remove_design(d_n)
        if d_n not in self.wg.get_design_names():
            file_convert(self.wg.driver, fn,d_n)
        self.delete_graphs.append(d_n)

        design = self.wg.get_design(d_n)
        pre_e = self.tg.edges()
        self.ppe.integrate_design(d_n)
        post_e = self.tg.edges()

        diff = list(set(post_e) - set(pre_e))
        self.diff_edges += diff
        for d in diff:
            exist = design.get_interactions(d.v.get_key())
            self.assertIn(d.v.get_key(),[e.v.get_key()for e in exist])
            self.assertIn(d.n.get_key(),[e.n.get_key()for e in exist])
            self.tg.interactions.negative(d.n,d.v,d.get_type())
    
    def test_integrate_design_synonym_uri(self):
        fn = os.path.join("files","test_integrate_design_synonym_uri.xml")
        d_n = "test_integrate_design_synonym_uri"
        self.wg.remove_design(d_n)
        if d_n not in self.wg.get_design_names():
            file_convert(self.wg.driver, fn,d_n)
        self.delete_graphs.append(d_n)
        design = self.wg.get_design(d_n)
        pre_e = self.tg.edges()
        self.ppe.integrate_design(d_n)
        post_e = self.tg.edges()

        diff = list(set(post_e) - set(pre_e))
        self.diff_edges += diff
        for d in diff:
            exist = design.get_interactions(d.v.get_key())
            if exist == []:
                exist = []
                for e in self.tg.synonyms.get(d.v).synonyms(d.v):
                    exist += design.get_interactions(e.v.get_key())
            self.assertIn(d.n.get_key(),[e.n.get_key()for e in exist])
            self.tg.interactions.negative(d.n,d.v,d.get_type())

    def test_integrate_design_direct_sequence(self):
        fn = os.path.join("files","test_integrate_design_direct_sequence.xml")
        d_n = "test_integrate_design_direct_sequence"
        self.wg.remove_design(d_n)
        if d_n not in self.wg.get_design_names():
            file_convert(self.wg.driver, fn,d_n)
        self.delete_graphs.append(d_n)
        design = self.wg.get_design(d_n)
        pre_e = self.tg.edges()
        self.ppe.integrate_design(d_n)
        post_e = self.tg.edges()

        diff = list(set(post_e) - set(pre_e))
        self.diff_edges += diff
        design_e_diff = list(set(design.get_physicalentity()) - 
                             set(self.tg.get_physicalentity()))
        design_e_diff = [d.get_key() for d in design_e_diff]
        # The design contains an interaction already in the TG.
        self.assertEqual(len(diff),2)
        for d in diff:
            if d.get_type() == nv_syn:
                self.assertIn(d.v.get_key(),design_e_diff)

    def test_integrate_design_fuzzy_uri(self):
        fn = os.path.join("files","test_integrate_design_fuzzy_uri.xml")
        d_n = "test_integrate_design_fuzzy_uri"
        self.wg.remove_design(d_n)
        if d_n not in self.wg.get_design_names():
            file_convert(self.wg.driver, fn,d_n)
        self.delete_graphs.append(d_n)
        design = self.wg.get_design(d_n)
        pre_e = self.tg.edges()
        self.ppe.integrate_design(d_n)
        post_e = self.tg.edges()

        diff = list(set(post_e) - set(pre_e))
        self.diff_edges += diff
        design_e_diff = list(set(design.get_physicalentity()) - 
                             set(self.tg.get_physicalentity()))
        design_e_diff = [d.get_key() for d in design_e_diff]
        for d in diff:
            if d.get_type() == nv_syn:
                self.assertIn(d.v.get_key(),design_e_diff)
                continue
            exist = design.get_interactions(d.v.get_key())
            if exist == []:
                exist = []
                for e in self.tg.synonyms.get(d.v).synonyms(d.v):
                    exist += design.get_interactions(e.v.get_key())
            self.assertIn(d.n.get_key(),[e.n.get_key()for e in exist])
            self.tg.interactions.negative(d.n,d.v,d.get_type())

    def test_integrate_design_indirect_sequence(self):
        fn = os.path.join("files","test_integrate_design_indirect_sequence.xml")
        d_n = "test_integrate_design_indirect_sequence"
        self.wg.remove_design(d_n)
        if d_n not in self.wg.get_design_names():
            file_convert(self.wg.driver, fn,d_n)
        self.delete_graphs.append(d_n)
        design = self.wg.get_design(d_n)
        pre_e = self.tg.edges()
        self.ppe.integrate_design(d_n)
        post_e = self.tg.edges()

        diff = list(set(post_e) - set(pre_e))
        self.diff_edges += diff
        design_e_diff = list(set(design.get_physicalentity()) - 
                             set(self.tg.get_physicalentity()))
        design_e_diff = [d.get_key() for d in design_e_diff]
        for d in diff:
            if d.get_type() == nv_syn:
                self.assertIn(d.v.get_key(),design_e_diff)
                continue
            exist = design.get_interactions(d.v.get_key())
            if exist == []:
                exist = []
                for e in self.tg.synonyms.get(d.v).synonyms(d.v):
                    exist += design.get_interactions(e.v.get_key())
            self.assertIn(d.n.get_key(),[e.n.get_key()for e in exist])
            self.tg.interactions.negative(d.n,d.v,d.get_type())


    def test_integrate_design_commonly_used(self):
        fn = os.path.join("files","canonical_AND.xml")
        d_n = "canonical_AND"
        self.wg.remove_design(d_n)
        if d_n not in self.wg.get_design_names():
            file_convert(self.wg.driver, fn,d_n)
        self.delete_graphs.append(d_n)
        design = self.wg.get_design(d_n)
        #self.ppe.integrate_design(d_n)
        u_graph = self.tg.usage.get()
        tg_entities = [e.get_key() for e in self.tg.get_physicalentity()]
        d_pgs = design.get_physicalentity()
        for entity in d_pgs:
            if entity.get_key() in tg_entities:
                self.assertTrue(u_graph.has_node(entity.get_key()))
            try:
                e_usage = [s.v.get_key() for s in u_graph.usage(entity.get_key())]
            except ValueError:
                continue
            for e1 in d_pgs:
                if entity == e1:
                    continue
                if e1.get_key() not in tg_entities:
                    continue
                self.assertIn(e1.get_key(),e_usage)




