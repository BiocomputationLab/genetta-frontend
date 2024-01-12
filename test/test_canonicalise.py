import sys
import os
import unittest

sys.path.insert(0, os.path.join(".."))
sys.path.insert(0, os.path.join("..",".."))
sys.path.insert(0, os.path.join("..","..",".."))
sys.path.insert(0, os.path.join("..","..","..",".."))
from app.graph.world_graph import WorldGraph
from app.tools.enhancer.enhancer import Enhancer
from app.converter.sbol_convert import convert
from app.converter.sbol_convert import export
from app.graph.utility.graph_objects.node import Node
from app.graph.utility.model.model import model

curr_dir = os.path.dirname(os.path.realpath(__file__))
fn = os.path.join("test","files","AND_gate.xml")

db_host = os.environ.get('NEO4J_HOST', 'localhost')
db_port = os.environ.get('NEO4J_PORT', '7687')
db_auth = os.environ.get('NEO4J_AUTH', "neo4j/Radeon12300")
db_auth = tuple(db_auth.split("/"))
uri = f'neo4j://{db_host}:{db_port}'
login_graph_name = "login_manager"

nv_cds = model.identifiers.objects.cds
nv_promoter = model.identifiers.objects.promoter
nv_has_seq = model.identifiers.predicates.hasSequence
nv_terminator = model.identifiers.objects.terminator
nv_desc = model.identifiers.external.description
class TestCanonical(unittest.TestCase):
    
    @classmethod
    def setUpClass(self):
        self.gn = "test_enhancer"
        self.wg = WorldGraph(uri,db_auth,reserved_names=[login_graph_name])
        self.enhancer = Enhancer(self.wg)
        self.miner = self.enhancer._miner
        self.wg.remove_design(self.gn)
        convert(fn,self.wg.driver,self.gn)
        self.canonicaliser = self.enhancer._canonicaliser
        


    @classmethod
    def tearDownClass(self):
        pass#self.wg.remove_design(self.gn)
    
    def test_get_truth_absolute(self):
        t_pes = self.wg.truth.get_physicalentity()

        # 1. Entity present.
        syns = self.wg.truth.synonyms.get()
        entity = list(syns.synonyms())[0].n
        res = self.canonicaliser._get_truth_absolute(entity,t_pes)
        self.assertEqual(entity,res[0])

        # 2. Synonym present.
        syn_e = list(syns.synonyms())[1]
        syn = syn_e.v
        res = self.canonicaliser._get_truth_absolute(syn,t_pes)
        self.assertEqual(syn_e.n,res[0])
        
        # 3. hasSeq present.
        entity = list(syns.synonyms())[2]
        props = {nv_has_seq : entity.n.hasSequence}
        node = Node("test_uri_no_identity",nv_cds,**props)
        res = self.canonicaliser._get_truth_absolute(node,t_pes)
        self.assertEqual(entity.n,res[0])


    def test_get_external_absolute(self):
        t_pes = self.wg.truth.get_physicalentity()
        # 1. Name is a record.
        key = "https://synbiohub.org/public/igem/BBa_B0015/1"
        node = Node(key,nv_terminator)
        res = self.canonicaliser._get_external_absolute(node,t_pes)
        self.assertEqual(node,res[0])
        
        # 2. Sequence maps to record.
        props = {nv_has_seq : '''atgagtgtgatcgctaaacaaatgacctacaaggttt
        atatgtcaggcacggtcaatggacactactttgaggtcgaaggcgatggaaaaggtaagccc
        tacgagggggagcagacggtaaagctcactgtcaccaagggcggacctctgccatttgcttg
        ggatattttatcaccacagtgtcagtacggaagcataccattcaccaagtaccctgaagaca
        tccctgactatgtaaagcagtcattcccggagggctatacatgggagaggatcatgaacttt
        gaagatggtgcagtgtgtactgtcagcaatgattccagcatccaaggcaactgtttcatcta
        ccatgtcaagttctctggtttgaactttcctcccaatggacctgtcatgcagaagaagacac
        agggctgggaacccaacactgagcgtctctttgcacgagatggaatgctgctaggaaacaac
        tttatggctctgaagttagaaggaggcggtcactatttgtgtgaatttaaaactacttacaa
        ggcaaagaagcctgtgaagatgccagggtatcactatgttgaccgcaaactggatgtaacca
        atcacaacaaggattacacttcggttgagcagtgtgaaatttccattgcacgcaaacctgtg
        gtcgcctaataa'''}
        key = "https://synbiohub.org/public/igem/BBa_K592009/1"
        node = Node("NO_Key_here",nv_cds,**props)
        expected_node = Node(key,nv_cds,**props)
        res = self.canonicaliser._get_external_absolute(node,t_pes)
        self.assertEqual(expected_node,res[0])


    def test_get_truth_potential(self):
        t_pes = self.wg.truth.get_physicalentity()

        # 1. Fuzzy String
        key = "TetRR"
        node = Node(key,nv_cds)
        expected = ["https://synbiohub.programmingbiology.org/public/Cello_Parts/TetR/1", 20]
        res = [(k,v) for k,v in self.canonicaliser._get_truth_potential(node,t_pes).items()]
        self.assertEqual([res[0][0].get_key(),res[0][1]],expected)

        # 2. Fuzzy & Synonym
        key = "LacI_sensorr"
        node = Node(key,nv_promoter)
        expected = ["https://synbiohub.programmingbiology.org/public/Cello_Parts/pTac/1", 30]
        res = [(k,v) for k,v in self.canonicaliser._get_truth_potential(node,t_pes).items()]
        self.assertEqual([res[0][0].get_key(),res[0][1]],expected)
         
        # 3. Partial sequence
        props = {nv_has_seq : '''CCGGTATCAGGCAATTTGAAGGTTGAGTTCTACAAC
        AGCAATCCTTCAGATACTACTAACTCAATCAATCCTCAGTTCAAGGTTACTAATACCGGAA
        GCAGTGCAATTGATTTGTCCAAACTCACATTGAGATATTATTATACAGTAGACGGACAGAA
        AGATCAGACCTTCTGGTGTGACCATGCTGCAATAATCGGCAGTAACGGCAGCTACAACGGA
        ATTACTTCAAATGTAAAAGGAACATTTGTAAAAATGAGTTCCTCAACAAATAACGCAGACA
        CCTACCTTGAAACTTTACAGGCGGAACTCTTGAACCGGGTGCACATGTTCAGATACA
        AGGTAGATTTGCAAAGAATGACTGGAGTAACTATACACAGTCAAATGACTACTCATTCAAG
        TCTGCTTCACAGTTTGTTGAATGATCAGGTAACAGCATACTTGAACGGTGTTCTTGTAT
        GGGGTAAAGAACCC'''}
        expected = ["https://synbiohub.org/public/igem/BBa_K2155005/1", 100]
        node = Node("NO_Key_here",nv_cds,**props)
        res = [(k,v) for k,v in self.canonicaliser._get_truth_potential(node,t_pes).items()]
        self.assertEqual(res[0][0].get_key(),expected[0])
        self.assertLess(res[0][1],100)
        self.assertGreater(res[0][1],90)
        
        # 3. Metadata
        key = "https://synbiohub.org/public/igem/L7Ae_myc-His6/1"
        node = Node(key,nv_cds)
        expected = ["https://synbiohub.org/public/igem/BBa_K1179079/1", 100]
        res = [(k,v) for k,v in self.canonicaliser._get_truth_potential(node,t_pes).items()]
        self.assertEqual([res[0][0].get_key(),res[0][1]],expected)


        key = "https://synbiohub.org/public/igem/Lex_A/1"
        node = Node(key,nv_cds)
        expected = ["https://synbiohub.org/public/igem/BBa_K1725200/1", 20]
        res = [(k,v) for k,v in self.canonicaliser._get_truth_potential(node,t_pes).items()]
        self.assertEqual([res[0][0].get_key(),res[0][1]],expected)


    def test_get_external_potential_entity_description(self):
        t_pes = self.wg.truth.get_physicalentity()
        # 1. Description has external entity
        key = "No_Key_Here"
        props = {nv_desc : ["TetR"]}
        node = Node(key,nv_cds,**props)
        expected = ["https://synbiohub.programmingbiology.org/public/Eco1C1G1T1/TetR/1", 50]
        res = [(k,v) for k,v in self.canonicaliser._get_external_potential(node,t_pes).items()]
        self.assertEqual([res[0][0].get_key(),res[0][1]],expected)


    def test_get_external_potential_entity_name(self):
        t_pes = self.wg.truth.get_physicalentity()
        # 1. Description has external entity
        key = "https://my_test_uri/TetR/1"
        node = Node(key,nv_cds)
        expected = (Node("https://synbiohub.programmingbiology.org/public/Eco1C1G1T1/TetR/1",
                         nv_cds), 50)
        res = [(k,v) for k,v in self.canonicaliser._get_external_potential(node,t_pes).items()]
        self.assertIn(expected,res)


    def _apply_canonical_test(self,synonym,canoncial):
        res = self.wg.truth.synonyms.get(canoncial)
        for r in res.edges():
            if r.v.get_key() == synonym and r.n.get_key() == canoncial:
                break
        else:
            self.fail()

        self.wg.truth.synonyms.negative(canoncial,synonym)
        res = self.wg.truth.synonyms.get(canoncial)
        for r in res.edges():
            if r.v.get_key() == synonym and r.n.get_key() == canoncial:
                self.fail()


    def test_apply(self):
        e_graph = self.wg.get_design(self.gn)
        for pe in e_graph.get_physicalentity():
            if hasattr(pe,"hasSequence"):
                subj = pe
                break
        subj_seq = subj.hasSequence
        test_key = "test_key123"
        t_seq = "ATCG"
        replacements = {subj.get_key():[test_key,subj.get_type(),{nv_has_seq:t_seq}]}
        replacements = self.canonicaliser.apply(replacements,self.gn)
        for e in e_graph.get_physicalentity():
            if test_key == e.get_key():
                self.assertEqual(e.hasSequence,t_seq)
                self.assertEqual([self.gn],e.graph_name)
                break
        else:
            self.fail()
    
        self._apply_canonical_test(subj.get_key(),test_key)
        replacements = {test_key:[subj.get_key(),subj.get_type(),{nv_has_seq:subj.hasSequence}]}
        self.canonicaliser.apply(replacements,self.gn)
        for e in e_graph.get_physicalentity():
            if subj.get_key() == e.get_key():
                self.assertEqual(e.hasSequence,subj_seq)
                break
        else:
            self.fail()
        self._apply_canonical_test(subj,test_key)


    def test_apply_overlap(self):
        e_graph = self.wg.get_design(self.gn)
        all_edges = e_graph.edges()
        for pe in e_graph.get_physicalentity():
            if hasattr(pe,"hasSequence"):
                subj = pe
                break
        subj_seq = subj.hasSequence
        test_key = "test_key123"
        t_seq = "ATCG"
        overlap_props = subj.properties
        overlap_props["graph_name"] = ["test_apply_overlap"]
        self.wg.driver.add_node(subj.get_key(),subj.get_type(),**overlap_props)
        self.wg.driver.submit()
        replacements = {subj.get_key():[test_key,subj.get_type(),{nv_has_seq:t_seq}]}
        self.canonicaliser.apply(replacements,self.gn)

        for e in e_graph.get_physicalentity():
            if test_key == e.get_key():
                self.assertEqual(e.hasSequence,t_seq)
                self.assertEqual([self.gn],e.graph_name)
                break
        else:
            self.fail()
        self._apply_canonical_test(subj,test_key)
        replacements = {test_key:[subj.get_key(),subj.get_type(),{nv_has_seq:subj.hasSequence}]}
        self.canonicaliser.apply(replacements,self.gn)
        for e in e_graph.get_physicalentity():
            if subj.get_key() == e.get_key():
                self.assertEqual(e.hasSequence,subj_seq)
                break
        else:
            self.fail()

        self._apply_canonical_test(subj,test_key)
        post_all_edges = e_graph.edges()
        self.assertCountEqual(all_edges,post_all_edges)

        subj.properties["graph_name"] = e_graph.name +["test_apply_overlap"]
        self.wg.driver.remove_node(subj)
        self.wg.driver.submit()


    def test_apply_and(self):
        e_graph = self.wg.get_design(self.gn)

        expected_internal = {
            "https://synbiohub.org/public/igem/my_rbs/1" : "https://synbiohub.programmingbiology.org/public/Cello_Parts/B3/1",
            "https://synbiohub.org/public/igem/BM3R1_repressor/1" : "https://synbiohub.programmingbiology.org/public/Cello_Parts/BM3R1/1",
            "https://synbiohub.programmingbiology.org/public/GokselEco1C1G1T2/SrpR/1" : "https://synbiohub.programmingbiology.org/public/Cello_Parts/SrpR/1",
            "https://synbiohub.org/public/igem/Tac_promoter/1" : "https://synbiohub.programmingbiology.org/public/Cello_Parts/pTac/1",
            "https://synbiohub.org/public/igem/Tet_promoter/1" : "https://synbiohub.programmingbiology.org/public/Cello_Parts/pTet/1",
            "https://synbiohub.org/public/igem/yellow_fluorescent_protein/1" : "https://synbiohub.org/public/igem/BBa_E0030/1"
        }
        
        expected_external = {
            "https://synbiohub.org/public/igem/DntR/1" : "https://synbiohub.org/public/igem/BBa_I723131/1",
            "https://synbiohub.org/public/igem/pPhIF/1" : "https://synbiohub.org/public/igem/BBa_K1899004/1",
            "https://synbiohub.org/public/igem/PhIF/1" : "https://synbiohub.org/public/igem/BBa_K1725040/1",
            "https://synbiohub.org/public/igem/PhIF_terminator/1" : "https://synbiohub.org/public/igem/BBa_J107115/1",
            "https://synbiohub.org/public/igem/L3S3P22/1" : "https://synbiohub.org/public/igem/BBa_J107113/1",
        }
        for k,v in expected_internal.items():
            res = self.wg.truth.node_query(v)
            self.assertEqual(len(res),1)
            expected_internal[k] = res[0]
        
        for k,v in expected_external.items():
            res = self.miner.record_to_node(self.miner.get(v),v)
            expected_external[k] = res

        replacements = expected_external
        replacements.update(expected_internal)
        self.canonicaliser.apply(replacements,self.gn)

        for k,v in replacements.items():
            self.assertEqual(e_graph.nodes(k),[])
            res = e_graph.nodes(v)
            self.assertEqual(len(res),1)
            self.assertEqual(res[0].get_key(),v.get_key())
            edges = e_graph.edges(v=res[0])
            self.assertEqual(len(edges),1)

            syns = self.wg.truth.synonyms.get(v.get_key())
            ders = self.wg.truth.derivatives.get(v.get_key())
            for r in syns.edges():
                if k == r.v.get_key():
                    break
            else:
                for d in ders.edges():
                    if k == d.v.get_key():
                        break
                else:
                    self.fail(f'{k} {v}')
            
        for k,v in replacements.items():
            self.wg.truth.synonyms.negative(k,v)
            self.wg.truth.derivatives.negative(k,v)


    def test_canonicalise_automated(self):
        pre_tg_e = self.wg.truth.edges()
        pre_tg_n = self.wg.truth.nodes()
        changes = self.enhancer.canonicalise(self.gn)
        expected_dict = {
            "https://synbiohub.org/public/igem/BM3R1_repressor/1" : ["https://synbiohub.programmingbiology.org/public/Cello_Parts/BM3R1/1"],
            "https://synbiohub.programmingbiology.org/public/GokselEco1C1G1T2/SrpR/1" : ["https://synbiohub.programmingbiology.org/public/Cello_Parts/SrpR/1"],
            "https://synbiohub.org/public/igem/Tet_promoter/1" : ["https://synbiohub.programmingbiology.org/public/Cello_Parts/pTet/1"],
            "https://synbiohub.org/public/igem/DntR/1" : ["https://synbiohub.org/public/igem/BBa_I723131/1"],
            }
        
        not_expected = [
            "https://synbiohub.org/public/igem/BBa_B0064/1",
            "https://synbiohub.org/public/igem/BBa_J133450/1",
            "https://synbiohub.programmingbiology.org/public/Cello_Parts/A1/1",
            "https://synbiohub.org/public/igem/my_rbs/1",
            "https://synbiohub.org/public/igem/Tac_promoter/1",
            "https://synbiohub.org/public/igem/yellow_fluorescent_protein/1",
            "https://synbiohub.org/public/igem/pPhIF/1",
            "https://synbiohub.org/public/igem/PhIF/1",
            "https://synbiohub.org/public/igem/PhIF_terminator/1",
            "https://synbiohub.org/public/igem/L3S3P22/1",
        ]
        for ne in not_expected:
            self.assertNotIn(ne,changes)
        for e_old,e_new in expected_dict.items():
            self.assertIn(e_old,changes)
            for element in e_new:
                self.assertEqual(element,str(changes[e_old]))
        e_graph = self.wg.get_design(self.gn)
        for k,v in changes.items():
            self.assertEqual(e_graph.nodes(k),[])
            res = e_graph.nodes(v)
            self.assertEqual(len(res),1)
            self.assertEqual(res[0].get_key(),v.get_key())
            edges = e_graph.edges(v=res[0])
            self.assertEqual(len(edges),1)

            syns = self.wg.truth.synonyms.get(v.get_key())
            ders = self.wg.truth.derivatives.get(v.get_key())
            for r in syns.edges():
                if k == r.v.get_key():
                    break
            else:
                for d in ders.edges():
                    if k == d.v.get_key():
                        break
                else:
                    self.fail(f'{k} {v}')
        
        post_tg_e = self.wg.truth.edges()
        diff_tg_e = list(set(post_tg_e) - set(pre_tg_e))
        self.wg.truth.remove_edges(diff_tg_e)

        post_tg_n = self.wg.truth.nodes()
        diff_tg_n = list(set(post_tg_n) - set(pre_tg_n))
        for tg_n in diff_tg_n:
            self.wg.truth.remove_node(tg_n)
        

    def test_canonicalise_manual(self):
        pre_tg = self.wg.truth.edges()
        changes = self.enhancer.canonicalise(self.gn,automated=False)
        expected_dict = {
            "https://synbiohub.org/public/igem/my_rbs/1" : [("https://synbiohub.programmingbiology.org/public/Cello_Parts/B3/1",94)],
            "https://synbiohub.org/public/igem/BM3R1_repressor/1" : [("https://synbiohub.programmingbiology.org/public/Cello_Parts/BM3R1/1",100)],
            "https://synbiohub.programmingbiology.org/public/GokselEco1C1G1T2/SrpR/1" : [("https://synbiohub.programmingbiology.org/public/Cello_Parts/SrpR/1",100)],
            "https://synbiohub.org/public/igem/Tac_promoter/1" : [("https://synbiohub.programmingbiology.org/public/Cello_Parts/pTac/1", 95)],
            "https://synbiohub.org/public/igem/Tet_promoter/1" : [("https://synbiohub.programmingbiology.org/public/Cello_Parts/pTet/1",100)],
            "https://synbiohub.org/public/igem/yellow_fluorescent_protein/1" : [("https://synbiohub.org/public/igem/BBa_E0030/1",40)],
            "https://synbiohub.org/public/igem/DntR/1" : [("https://synbiohub.org/public/igem/BBa_I723131/1",100)],
            "https://synbiohub.org/public/igem/pPhIF/1" : [("https://synbiohub.org/public/igem/BBa_K1899004/1",20)],
            "https://synbiohub.org/public/igem/PhIF/1" : [("https://synbiohub.org/public/igem/BBa_K1725040/1",30)],
            "https://synbiohub.org/public/igem/PhIF_terminator/1" : [("https://synbiohub.org/public/igem/BBa_J107115/1",50)],
            "https://synbiohub.org/public/igem/L3S3P22/1" : [("https://synbiohub.org/public/igem/BBa_J107113/1",50)]
            }
        
        not_expected = [
            "https://synbiohub.org/public/igem/BBa_B0064/1",
            "https://synbiohub.org/public/igem/BBa_J133450/1",
            "https://synbiohub.programmingbiology.org/public/Cello_Parts/A1/1",
        ]
        for ne in not_expected:
            self.assertNotIn(ne,changes)
        for e_old,e_new in expected_dict.items():
            self.assertIn(e_old,changes)
            for element in e_new:
                actual = [(str(k),v) for k,v in changes[e_old]]
                self.assertIn(element,actual)
        feedback = {k:o[0][0] for k,o in changes.items()}
    
        self.enhancer.apply_canonicalise(feedback,self.gn)
        e_graph = self.wg.get_design(self.gn)
        for k,v in feedback.items():
            self.assertEqual(e_graph.nodes(k),[])
            res = e_graph.nodes(v)
            self.assertEqual(len(res),1)
            self.assertEqual(res[0].get_key(),v.get_key())
            edges = e_graph.edges(v=res[0])
            self.assertEqual(len(edges),1)

            syns = self.wg.truth.synonyms.get(v.get_key())
            ders = self.wg.truth.derivatives.get(v.get_key())
            for r in syns.edges():
                if k == r.v.get_key():
                    break
            else:
                for d in ders.edges():
                    if k == d.v.get_key():
                        break
                else:
                    self.fail(f'{k} {v}')
            
        post_tg = self.wg.truth.edges()
        diff_tg = list(set(post_tg) - set(pre_tg))
        self.wg.truth.remove_edges(diff_tg)



    def test_canonicalise_full(self):
        t_fn = os.path.join("test","files","nor_full.xml")
        gn = "test_canonicalise_full"
        self.wg.remove_design(gn)
        convert(t_fn,self.wg.driver,gn)
        graph = self.wg.get_design(gn)
        changes = self.enhancer.canonicalise(gn,automated=False)
        self.wg.remove_design(gn)