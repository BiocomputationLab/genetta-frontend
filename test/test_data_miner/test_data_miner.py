import sys
import os
import unittest
from rdflib import Graph, URIRef
sys.path.insert(0, os.path.join(".."))
sys.path.insert(0, os.path.join("..",".."))
sys.path.insert(0, os.path.join("..","..",".."))
sys.path.insert(0, os.path.join("..","..","..",".."))
from app.graph.world_graph import WorldGraph
from app.tools.enhancer.enhancer import Enhancer
from app.graph.utility.model.model import model
curr_dir = os.path.dirname(os.path.realpath(__file__))
fn = os.path.join("test","files","nor_full.xml")

class TestDataMiner(unittest.TestCase):
    
    @classmethod
    def setUpClass(self):
        self.gn = "test_enhancer"
        self.wg = WorldGraph()
        self.enhancer = Enhancer(self.wg)
        self.miner = self.enhancer._miner

    @classmethod
    def tearDownClass(self):
        pass

    def test_is_reference(self):
        self.assertFalse(self.miner.is_reference("1"))
        self.assertTrue(self.miner.is_reference("http://sevahub.es/public/Canonical/pSEVA111/1"))
        self.assertFalse(self.miner.is_reference("https://synbiohub.programmingbiology.org/public/GokselEco1C1G1T2/A1_AmtR/1123"))
        self.assertFalse(self.miner.is_reference(""))

    def test_get(self):
        r = self.miner.get("https://synbiohub.programmingbiology.org/public/GokselEco1C1G1T2/A1_AmtR/1")
        r1 = self.miner.get("A1_AmtR")
        r_trips = list(set(r.triples((None,None,None))) - set(r1.triples((None,None,None))))
        self.assertEqual(len(r_trips),0)
        r3 = self.miner.get("tst")
        self.assertIsNone(r3)

    def test_sequence_match(self):
        sequence = "agctttaagaaggagatatacataatggcaatggcagcatctcgtcaggctgttcgcgttgcagcagctgtggatgctgattaccgtaagcgcgaaccaaaggacgtgcgcgtgcttgttgtaggtccaacaggttacatcggtaagttcgtggtgaaggaactcgtgagccgtggttacaacgtggttgcattcgcacgtgagaatgcaggtatcaagggtaagatgggtcgtgaagatatcgtgaaggagttccatggtgcggaagtgcgtttcggttctgtgctggatccagcttcgctgcgtgacgttgcattcaaggacccagttgacgttgttgttagctgcctggcaagccgcacaggtggtaagaaggactcgtggctgatcgactacacagctactaagaacagcctggacgttgcacgcgcatctggtgcaaagcactttgtgctgctgtctgcaatctgcgtgcagaagccactgctggagttccagaaagccaagctccagttcgagtctgaccttcaggctgccggtgacatcacctattccatcgtgcgtcctaccgcattcttcaagtccattgctggtcagatcgacatcgtgaagaaaggtaacccatacgtcatgtttggtgacggtaacctggcagcatgcaaacctatcagcgaagctgacctggcttcattcattgcagattgcgtcaccgaacagaacaaggtcaacaaggtgctgcctatcggtggtccaagcaaggccttcacggctaagcagcaggctgatctgctgttcaacatcacaggtctgccacctaagtacttccctgtgcctgtggcactcatggatggtatgattggtctgttcgactctctggctaagctgttcccacagctggaagatagcgctgaatttgcacgtattggtaagtactatgccaccgaatccatgctggtgtacgacgaggcacgtggtgtgtaccggaagacgaaacgcctggttacggcaaggacacgctggaagacttcttctctcgtgcagtgaaggaaggtctgcaaggacaggaactgggtgaccaggcagtgtttggacaacaataataataa"
        match = self.miner.sequence_match(sequence)
        self.assertEqual(str(match),"https://synbiohub.org/public/igem/BBa_K1080012/1")
    
    def test_get_subject(self):
        fn = os.path.join("files","laci_synbiohub.xml")
        g = Graph()
        g.parse(fn)
        res = self.miner.get_subject(g)   
        self.assertEqual(str(res),"https://synbiohub.org/public/igem/BBa_R0010/1")

        fn = os.path.join("files","nor_full.xml")
        g = Graph()
        g.parse(fn)
        res = self.miner.get_subject(g,["Ara_"])
        self.assertEqual(str(res),"http://shortbol.org/v2#Ara_arac/1")

    def test_mine_explicit_references(self):
        meta = ["BBa_K143012"]
        refs = self.miner.mine_explicit_reference(meta)
        self.assertEqual(refs,URIRef("https://synbiohub.org/public/igem/BBa_K143012/1"))

        meta = ["Represses: BBa_K143012"]
        refs = self.miner.mine_explicit_reference(meta)
        self.assertEqual(refs,None)

        meta = ["Represses","","1","1-1","Repressor for this."]
        refs = self.miner.mine_explicit_reference(meta)
        self.assertEqual(refs,None)

    def test_query(self):
        dbs = list(self.miner._database._db_util.db_mapping_calls.keys())
        for index,db_res in enumerate(self.miner.query("laci")):
            db = dbs[index]
            for res in db_res:
                self.assertTrue(self.miner._database.is_record(res) or self.miner._database._db_util.get(res,db) is not None)
        dbs = list(self.miner._database._db_util.db_mapping_calls.keys())
        db_res = list(self.miner.query("laci",lazy=True))
        self.assertEqual(len(db_res),1)
        db_res = db_res[0]
        for res in db_res:
            self.assertTrue(self.miner._database.is_record(res) or self.miner._database._db_util.get(res,db) is not None)



