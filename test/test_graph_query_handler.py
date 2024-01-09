import sys
import os
import unittest
import random
sys.path.insert(0, os.path.join(".."))
sys.path.insert(0, os.path.join("..",".."))
sys.path.insert(0, os.path.join("..","..",".."))
sys.path.insert(0, os.path.join("..","..","..",".."))

from app.tools.graph_query.handler import GraphQueryHandler
from app.tools.graph_query.datatype_handlers.sequence import SequenceHandler
from app.tools.graph_query.datatype_handlers.modules import ModuleHandler
from app.graph.world_graph import WorldGraph
from app.tools.aligner import aligner
from app.graph.utility.model.model import model
from app.graph.utility.graph_objects.reserved_edge import ReservedEdge
from app.graph.utility.graph_objects.reserved_node import ReservedNode
curr_dir = os.path.dirname(os.path.realpath(__file__))

db_host = os.environ.get('NEO4J_HOST', 'localhost')
db_port = os.environ.get('NEO4J_PORT', '7687')
db_auth = os.environ.get('NEO4J_AUTH', "neo4j/Radeon12300")
db_auth = tuple(db_auth.split("/"))
uri = f'neo4j://{db_host}:{db_port}'
login_graph_name = "login_manager"

confidence = str(model.identifiers.external.confidence)
p_synonym = str(model.identifiers.external.synonym)
p_derivative = str(model.identifiers.external.derivative)
p_template = str(model.identifiers.predicates.template)
o_cds = str(model.identifiers.objects.cds)
o_gp = str(model.identifiers.objects.genetic_production)

class TestGraphQueryHandlerCanonical(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self._wg = WorldGraph(uri,db_auth)
        self._handlers = GraphQueryHandler(self._wg.truth)
        self._tg = self._wg.truth

    def test_query_input_name(self):
        qry_str = "pTet"
        expected_result = "https://synbiohub.programmingbiology.org/public/Cello_Parts/pTet/1"
        res = self._handlers.query("Canonical",qry_str)
        self.assertIn(qry_str,res)
        self.assertIn(expected_result,[s[1]["entity"] for s in res[qry_str]])

    def test_query_input_uri(self):
        qry_str = "https://synbiohub.org/public/igem/BBa_I753000/1"
        expected_result = "https://synbiohub.org/public/igem/BBa_Z52934/1"
        res = self._handlers.query("Canonical",qry_str)
        self.assertIn(qry_str,res)
        self.assertIn(expected_result,[s[1]["entity"] for s in res[qry_str]])

    def test_query_input_varied(self):
        qry_part1 = "TetR_sensor"
        qry_part2 = "https://synbiohub.programmingbiology.org/public/GokselEco1C1G1T2/pTet/1"
        expected_result = "https://synbiohub.programmingbiology.org/public/Cello_Parts/pTet/1"
        res = self._handlers.query("Canonical",f'{qry_part1} {qry_part2}')
        self.assertEqual(len(res),2)
        self.assertIn(qry_part1,res)
        self.assertIn(expected_result,[s[1]["entity"] for s in res[qry_part1]])
        self.assertIn(qry_part2,res)
        self.assertIn(expected_result,[s[1]["entity"] for s in res[qry_part2]])

    def test_query_input_varied2(self):
        qry_part1 = "Give me all entities that are "
        qry_part2 = "TetR_sensor"
        expected_result = "https://synbiohub.programmingbiology.org/public/Cello_Parts/pTet/1"
        res = self._handlers.query("Canonical",f'{qry_part1} {qry_part2}')
        self.assertIn(qry_part2,res)
        self.assertIn(expected_result,[s[1]["entity"] for s in res[qry_part2]])

    def test_query_input_canonical(self):
        qry_str = "https://synbiohub.programmingbiology.org/public/Cello_Parts/pTet/1"
        expected_result = [100,"https://synbiohub.programmingbiology.org/public/Cello_Parts/pTet/1"]
        res = self._handlers.query("Canonical",qry_str)
        self.assertEqual(len(res),1)
        self.assertIn(qry_str,res)
        self.assertEqual(res[qry_str][0][0],expected_result[0])
        self.assertEqual(res[qry_str][0][1]["entity"],expected_result[1])

    def test_feedback_name(self):
        inp_source = "pTet_test" 
        inp_res = "https://synbiohub.programmingbiology.org/public/Cello_Parts/pTet/1"

        e_n_n1 = ReservedNode(inp_res,model.identifiers.objects.promoter,graph_name=self._tg.name)
        e_n_n2 = ReservedNode(inp_source,None,graph_name=self._tg.name)
        e_n_e = ReservedEdge(e_n_n1,e_n_n2,p_synonym,graph_name=self._tg.name)
        pre_graph = self._tg.synonyms.get(inp_res)
        pre_edges = list(pre_graph.synonyms())
        try:
            pre_conf = [e.confidence for e in pre_edges if e.v.get_key() == inp_source][0]
        except IndexError:
            pre_conf = 0

        self._handlers.feedback("Canonical",inp_source,inp_res)
        post_graph = self._tg.synonyms.get(inp_res)
        post_edges = list(post_graph.synonyms(),)
        diff = list(set(post_edges) - set(pre_edges))
        self.assertEqual(len(diff), 1)
        self.assertEqual(diff[0],e_n_e)
        for e in post_edges:
            if e.v.get_key() == inp_source:
                self.assertEqual(e.confidence,pre_conf + self._tg.synonyms._standard_modifier)

        self._handlers.feedback("Canonical",inp_source,inp_res,positive=False)
        post_graph = self._tg.synonyms.get(inp_res)
        post_edges = list(post_graph.synonyms())
        diff = list(set(post_edges) - set(pre_edges))
        self.assertTrue(len(diff) == 0)
        for e in post_edges:
            if e.v.get_key() == inp_source:
                self.assertEqual(e.confidence,pre_conf)

    def test_feedback_uri(self):
        inp_source = "https://synbiohub.org/public/igem/BBa_I753000/1" 
        inp_res = "https://synbiohub.org/public/igem/BBa_Z52934/1"
        pre_graph = self._tg.synonyms.get(inp_res)
        pre_edges = list(pre_graph.synonyms())
        pre_conf = [e.confidence for e in pre_edges if e.v.get_key() == inp_source][0]

        self._handlers.feedback("Canonical",inp_source,inp_res,positive=False)
        post_graph = self._tg.synonyms.get(inp_res)
        post_edges = list(post_graph.synonyms())
        diff = list(set(post_edges) - set(pre_edges))
        self.assertTrue(len(diff) == 0)
        for e in post_edges:
            if e.v.get_key() == inp_source:
                self.assertEqual(e.confidence,pre_conf - self._tg.synonyms._standard_modifier)

        self._handlers.feedback("Canonical",inp_source,inp_res)
        post_graph = self._tg.synonyms.get(inp_res)
        post_edges = list(post_graph.synonyms())
        diff = list(set(post_edges) - set(pre_edges))
        self.assertTrue(len(diff) == 0)
        for e in post_edges:
            if e.v.get_key() == inp_source:
                self.assertEqual(e.confidence,pre_conf)

class TestGraphQueryHandlerDerivative(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self._wg = WorldGraph(uri,db_auth)
        self._handlers = GraphQueryHandler(self._wg.truth)
        self._tg = self._wg.truth

    def test_query_input_uri(self):
        qry_str = "https://synbiohub.org/public/igem/BBa_K199198/1"
        expected_result = [(99, 'https://synbiohub.org/public/igem/BBa_J31007/1'), 
                           (97, 'https://synbiohub.org/public/igem/BBa_K315021/1'), 
                           (96, 'https://synbiohub.org/public/igem/BBa_K315015/1'), 
                           (96, 'https://synbiohub.org/public/igem/BBa_K137052/1'), 
                           (95, 'https://synbiohub.org/public/igem/BBa_K315040/1'), 
                           (83, 'https://synbiohub.org/public/igem/BBa_K137100/1')]
        res = self._handlers.query("Derivative",qry_str)
        self.assertEqual(len(res),1)
        self.assertIn(qry_str,res)
        for index,e in enumerate(res[qry_str]):
            self.assertEqual(e[0],expected_result[index][0])
            self.assertEqual(e[1]["entity"],expected_result[index][1])

    def test_query_input_name(self):
        qry_str = "S2"
        expected_key = "https://synbiohub.programmingbiology.org/public/Cello_Parts/S2/1"
        expected_result = [92, 'https://synbiohub.programmingbiology.org/public/Cello_Parts/S3/1']
        res = self._handlers.query("Derivative",qry_str)
        self.assertIn(expected_key,res)
        self.assertEqual(res[expected_key][0][0],expected_result[0])
        self.assertEqual(res[expected_key][0][1]["entity"],expected_result[1])

    def test_query_input_synonym(self):
        qry_str = "https://synbiohub.org/public/igem/BBa_K1583061/1"
        expected_result = [(91, 'https://synbiohub.org/public/igem/BBa_K1676013/1'), 
                            (91, 'https://synbiohub.org/public/igem/BBa_K1676032/1'), 
                            (91, 'https://synbiohub.org/public/igem/BBa_K1676007/1'), 
                            (91, 'https://synbiohub.org/public/igem/BBa_K1676036/1'), 
                            (91, 'https://synbiohub.org/public/igem/BBa_K1676012/1'), 
                            (91, 'https://synbiohub.org/public/igem/BBa_K1676033/1'), 
                            (91, 'https://synbiohub.org/public/igem/BBa_K1676014/1'), 
                            (91, 'https://synbiohub.org/public/igem/BBa_K1676029/1'), 
                            (91, 'https://synbiohub.org/public/igem/BBa_K1676035/1'), 
                            (91, 'https://synbiohub.org/public/igem/BBa_K1676028/1'), 
                            (91, 'https://synbiohub.org/public/igem/BBa_K1676030/1'), 
                            (91, 'https://synbiohub.org/public/igem/BBa_K1676025/1'), 
                            (91, 'https://synbiohub.org/public/igem/BBa_K1676015/1'), 
                            (91, 'https://synbiohub.org/public/igem/BBa_K1676034/1'), 
                            (91, 'https://synbiohub.org/public/igem/BBa_K1676031/1'), 
                            (83, 'https://synbiohub.org/public/igem/BBa_J23080/1'), 
                            (83, 'https://synbiohub.org/public/igem/BBa_J61109/1')]
        expected_key = "https://synbiohub.org/public/igem/BBa_J34801/1"
        res = self._handlers.query("Derivative",qry_str)
        self.assertEqual(len(res),1)
        self.assertIn(expected_key,res)
        for e in res[expected_key]:
            self.assertIn(e[0],[e[0] for e in expected_result])
            self.assertIn(e[1]["entity"],[e[1] for e in expected_result])

    def test_query_input_varied(self):
        qry_part1 = "BBa_K228000"
        qry_part2 = "https://synbiohub.org/public/igem/BBa_K823013/1"
        expected_result2 = [(97, 'https://synbiohub.org/public/igem/BBa_J23104/1'), 
                            (94, 'https://synbiohub.org/public/igem/BBa_J23102/1'), 
                            (94, 'https://synbiohub.org/public/igem/BBa_J23116/1'), 
                            (94, 'https://synbiohub.org/public/igem/BBa_J23109/1'), 
                            (91, 'https://synbiohub.org/public/igem/BBa_J23103/1'), 
                            (91, 'https://synbiohub.org/public/igem/BBa_J23101/1'), 
                            (88, 'https://synbiohub.org/public/igem/BBa_J72075/1')]
        
        expected_result1 = [(99, 'https://synbiohub.org/public/igem/BBa_K199171/1'), 
                            (99, 'https://synbiohub.org/public/igem/BBa_I2032/1'), 
                            (95, 'https://synbiohub.org/public/igem/BBa_K784048/1')]
        expected_key = "https://synbiohub.org/public/igem/BBa_K228000/1"
        res = self._handlers.query("Derivative",f'{qry_part1} {qry_part2}')
        self.assertIn(expected_key,res)
        for e in res[expected_key]:
            self.assertIn(e[0],[e[0] for e in expected_result1])
            self.assertIn(e[1]["entity"],[e[1] for e in expected_result1])

        self.assertIn(qry_part2,res)
        for e in res[qry_part2]:
            self.assertIn(e[0],[e[0] for e in expected_result2])
            self.assertIn(e[1]["entity"],[e[1] for e in expected_result2])
    
    def test_query_input_varied2(self):
        qry_part1 = "Give me all entities that are similar to "
        qry_part2 = "https://synbiohub.org/public/igem/BBa_K100000/1"
        expected_result = [98, 'https://synbiohub.org/public/igem/BBa_K100001/1']
        res = self._handlers.query("Derivative",f'{qry_part1} {qry_part2}')
        self.assertEqual(len(res),1)
        self.assertIn(qry_part2,res)
        self.assertEqual(res[qry_part2][0][0],expected_result[0])
        self.assertEqual(res[qry_part2][0][1]["entity"],expected_result[1])

    def test_feedback_name(self):
        inp_source = "https://synbiohub.org/public/bsu/BO_10626/1" 
        inp_res = "https://synbiohub.programmingbiology.org/public/Cello_Parts/pTet/1"

        e_n_n1 = ReservedNode(inp_res,model.identifiers.objects.promoter,graph_name=self._tg.name)
        e_n_n2 = ReservedNode(inp_source,model.identifiers.objects.protein,graph_name=self._tg.name)
        e_n_e = ReservedEdge(e_n_n1,e_n_n2,p_derivative,graph_name=self._tg.name)
        pre_graph = self._tg.derivatives.get(inp_res,threshold=5)
        pre_edges = list(pre_graph.derivatives())
        try:
            pre_conf = [e.confidence for e in pre_edges if e.v.get_key() == inp_source][0]
        except IndexError:
            pre_conf = 0

        self._handlers.feedback("Derivative",inp_source,inp_res)
        post_graph = self._tg.derivatives.get(inp_res,threshold=0)
        post_edges = list(post_graph.derivatives())
        diff = list(set(post_edges) - set(pre_edges))
        self.assertEqual(len(diff), 1)
        self.assertEqual(diff[0],e_n_e)
        for e in post_edges:
            if e.v.get_key() == inp_source:
                self.assertEqual(e.confidence,pre_conf + self._tg.derivatives._standard_modifier)

        self._handlers.feedback("Derivative",inp_source,inp_res,positive=False)
        post_graph = self._tg.derivatives.get(inp_res,threshold=5)
        post_edges = list(post_graph.derivatives())
        diff = list(set(post_edges) - set(pre_edges))
        self.assertTrue(len(diff) == 0)
        for e in post_edges:
            if e.v.get_key() == inp_source:
                self.assertEqual(e.confidence,pre_conf)

class TestGraphQueryHandlerInteraction(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self._wg = WorldGraph(uri,db_auth)
        self._handlers = GraphQueryHandler(self._wg.truth)
        self._tg = self._wg.truth

    def test_query_input_uri(self):
        qry_str = "https://synbiohub.programmingbiology.org/public/Cello_Parts/HlyIIR_protein/1"
        res = self._handlers.query("Interaction",qry_str)

        expected_ints = ["https://synbiohub.programmingbiology.org/public/Cello_Parts/HlyIIR_protein_production/HlyIIR_protein_interaction/1",
                        "https://synbiohub.programmingbiology.org/public/Cello_Parts/HlyIIR_protein_degradation/HlyIIR_degradation_interaction/1",
                        "https://synbiohub.programmingbiology.org/public/Cello_Parts/HlyIIR_pHlyIIR_repression/HlyIIR_pHlyIIR_repression/1",
                        "https://synbiohub.programmingbiology.org/public/GokselEco1C1G1T2/HlyIIR_protein_pHlyIIR_repression/HlyIIR_protein_pHlyIIR_repression/1"]
        for subj,entities in res.items():
            self.assertEqual(subj,qry_str)
            for conf,elements in entities:
                entity = elements["entity"]
                self.assertIn(entity,expected_ints)


    def test_query_input_name(self):
        qry_str = "pTet"
        expected_key = "https://synbiohub.programmingbiology.org/public/Cello_Parts/pTet/1"
        expected_int = "https://synbiohub.programmingbiology.org/public/Cello_Parts/TetR_pTet_repression/TetR_pTet_repression/1"
        res = self._handlers.query("Interaction",qry_str)
        self.assertIn(expected_key,res)
        self.assertIn(expected_int,[s[1]["entity"] for s in res[expected_key]])


    def test_query_input_varied(self):
        qry_part1 = "BO_26996"
        qry_part2 = "https://synbiohub.programmingbiology.org/public/GokselEco1C1G1T2/pTet/1"
        expected_result = {"https://synbiohub.programmingbiology.org/public/Cello_Parts/pTet/1" : ["https://synbiohub.programmingbiology.org/public/Cello_Parts/TetR_pTet_repression/TetR_pTet_repression/1"],
                           "https://synbiohub.org/public/bsu/BO_26996/1" : ["https://synbiohub.org/public/bsu/module_BO_26996_activates_BO_3314/BO_26996_activates_BO_3314/1",
                                                                            "https://synbiohub.org/public/bsu/module_BO_26996_represses_BO_2996/BO_26996_represses_BO_2996/1",
                                                                            "https://synbiohub.org/public/bsu/module_BO_26996_activates_BO_2928/BO_26996_activates_BO_2928/1",
                                                                            "https://synbiohub.org/public/bsu/module_BO_26996_activates_BO_27780/BO_26996_activates_BO_27780/1",
                                                                            "https://synbiohub.org/public/bsu/module_BO_26996_activates_BO_2815/BO_26996_activates_BO_2815/1",
                                                                            "https://synbiohub.org/public/bsu/module_BO_26996_activates_BO_3311/BO_26996_activates_BO_3311/1",
                                                                            "https://synbiohub.org/public/bsu/module_BO_26996_activates_BO_2938/BO_26996_activates_BO_2938/1",
                                                                            "https://synbiohub.org/public/bsu/module_BO_32743_encodes_BO_26996/BO_32743_encodes_BO_26996/1",
                                                                            "https://synbiohub.org/public/bsu/module_BO_26996_activates_BO_2937/BO_26996_activates_BO_2937/1",
                                                                            "https://synbiohub.org/public/bsu/module_BO_26996_represses_BO_27751/BO_26996_represses_BO_27751/1",
                                                                            "https://synbiohub.org/public/bsu/module_BO_26996_activates_BO_3314/BO_26996_activates_BO_3314/1",
                                                                            "https://synbiohub.org/public/bsu/module_BO_26996_represses_BO_2996/BO_26996_represses_BO_2996/1"]}
        res = self._handlers.query("Interaction",f'{qry_part1} {qry_part2}')
        self.assertGreater(len(res),0)
        for subj,entities in expected_result.items():
            self.assertIn(subj,res)
            for entity in entities:
                self.assertIn(entity,[r[1]["entity"] for r in res[subj]])


    def test_query_input_varied2(self):
        qry_part1 = "Give me all entities that are "
        qry_part2 = "LacI_sensors"
        expected_result = {"https://synbiohub.programmingbiology.org/public/Cello_Parts/pTac/1" : 
                           ["https://synbiohub.programmingbiology.org/public/Cello_Parts/LacI_pTac_repression/LacI_pTac_repression/1"],}
        res = self._handlers.query("Interaction",f'{qry_part1} {qry_part2}')
        self.assertGreater(len(res),0)
        for subj,entities in expected_result.items():
            self.assertIn(subj,res)
            for entity in entities:
                self.assertIn(entity,[r[1]["entity"] for r in res[subj]])


    def test_feedback_existing(self):
        inp_source = "https://synbiohub.programmingbiology.org/public/Cello_Parts/IcaRA/1" 
        inp_res = "https://synbiohub.programmingbiology.org/public/Cello_Parts/IcaRA_protein_production/IcaRA_protein_interaction/1"
        e_n_n1 = ReservedNode(inp_res,o_cds,graph_name=self._tg.name)
        e_n_n2 = ReservedNode(inp_source,o_gp,graph_name=self._tg.name)
        pre_graph = self._tg.interactions.get(inp_res)
        pre_edges = list(pre_graph.interactions())
        try:
            pre_conf = [e.confidence for e in pre_edges if e.v.get_key() == inp_source][0]
        except IndexError:
            pre_conf = 0

        self._handlers.feedback("Interaction",inp_source,inp_res)
        post_graph = self._tg.interactions.get(inp_res)
        post_edges = list(post_graph.interactions(),)
        diff = list(set(post_edges) - set(pre_edges))
        for e in post_edges:
            if e.v.get_key() == inp_source:
                self.assertEqual(e.confidence,pre_conf + self._tg.interactions._standard_modifier)

        self._handlers.feedback("Interaction",inp_source,inp_res,positive=False)
        post_graph = self._tg.interactions.get(inp_res)
        post_edges = list(post_graph.interactions())
        diff = list(set(post_edges) - set(pre_edges))
        self.assertTrue(len(diff) == 0)
        for e in post_edges:
            if e.v.get_key() == inp_source:
                self.assertEqual(e.confidence,pre_conf)

class TestGraphQueryHandlerMetadata(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self._wg = WorldGraph(uri,db_auth)
        self._handlers = GraphQueryHandler(self._wg.truth)
        self._tg = self._wg.truth

    def test_query_single(self):
        qry_str = "LacI- wild type"
        expected_result = "https://synbiohub.org/public/igem/BBa_K091122/1"
        res = self._handlers.query("Metadata",qry_str)
        for k,v in res.items():
            for e in v:
                if e[1]["entity"] == expected_result:
                    break
            else:
                self.fail()

class TestGraphQueryHandlerSequence(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self._wg = WorldGraph(uri,db_auth)
        self._handlers = SequenceHandler(self._wg.truth)
        self._tg = self._wg.truth

    def test_sequence_query_direct_match(self):
        d_graph = self._tg.derivatives.get()
        for entity in self._tg.get_dna():
            res = self._handlers.handle(entity.hasSequence)
            self.assertIn(entity.get_key(),res)
            self.assertIn(entity.get_key(),[e[1]["entity"] for e in 
                                            res[entity.get_key()]])
            ders = list(d_graph.derivatives(entity))
            der_names = [d.v.get_key() for d in ders]
            for r_entity,d_entities in res.items():
                self.assertEqual(entity.get_key(),r_entity)
                for d_entity in d_entities:
                    if entity.get_key() == d_entity[1]["entity"]:
                        continue
                    self.assertIn(d_entity[1]["entity"],der_names)
                    e_conf = [e.confidence for e in ders if 
                              e.v.get_key() == d_entity[1]["entity"]][0]
                    self.assertEqual(d_entity[0], e_conf)

    def test_sequence_query_partial_match(self):
        for entity in self._tg.get_dna():
            # Sample, the full dataset is quite big.
            if random.randint(0,500) != 1:
                continue
            diff = random.randint(0, 100)    
            ms = make_random_changes(entity.hasSequence,diff)
            res = self._handlers.handle(ms)
            if len(res) == 0:
                score = int(aligner.sequence_match(entity.hasSequence,ms)*100)
                self.assertGreaterEqual(self._handlers._threshold,score)
            if diff == 0:
                self.assertIn(entity.get_key(),res)
                self.assertIn(entity.get_key(),[e[1]["entity"] for e in 
                                                res[entity.get_key()]])
                continue
            for source,d_entities in res.items():
                self.assertEqual(source,None)
                for score,entity in d_entities:
                    self.assertGreaterEqual(score,self._handlers._threshold)

    def test_feedback_indirect_match(self):
        source = None
        result = "https://synbiohub.org/public/igem/BBa_K1676024/1"
        self._handlers.feedback(source,result)
        pre_graph = self._tg.derivatives.get(result,threshold=5)
        pre_edges = list(pre_graph.derivatives())
        try:
            pre_conf = [e.confidence for e in pre_edges if e.v.get_key() == result][0]
        except IndexError:
            pre_conf = 0

        self._handlers.feedback(source,result)
        post_graph = self._tg.derivatives.get(result,threshold=5)
        post_edges = list(post_graph.derivatives())
        diff = list(set(post_edges) - set(pre_edges))
        self.assertEqual(len(diff), 0)
        for e in post_edges:
            if e.v.get_key() == result:
                self.assertEqual(e.confidence,pre_conf)

    def test_feedback_identical(self):
        source = "https://synbiohub.org/public/igem/BBa_K1676024/1"
        result = "https://synbiohub.org/public/igem/BBa_K1676024/1"
        self._handlers.feedback(source,result)
        pre_graph = self._tg.derivatives.get(result,threshold=5)
        pre_edges = list(pre_graph.derivatives())
        try:
            pre_conf = [e.confidence for e in pre_edges if e.v.get_key() == result][0]
        except IndexError:
            pre_conf = 0

        self._handlers.feedback(source,result)
        post_graph = self._tg.derivatives.get(result,threshold=5)
        post_edges = list(post_graph.derivatives())
        diff = list(set(post_edges) - set(pre_edges))
        self.assertEqual(len(diff), 0)
        for e in post_edges:
            if e.v.get_key() == result:
                self.assertEqual(e.confidence,pre_conf)

    def test_feedback_direct_match(self):
        source = "https://synbiohub.org/public/igem/BBa_J34801/1"
        result = "https://synbiohub.org/public/igem/BBa_K1676030/1"
        pre_graph = self._tg.derivatives.get(result,threshold=5)
        pre_edges = list(pre_graph.derivatives())
        try:
            pre_conf = [e.confidence for e in pre_edges if e.n.get_key() == result][0]
        except IndexError:
            pre_conf = 0

        self._handlers.feedback(source,result)
        post_graph = self._tg.derivatives.get(result,threshold=5)
        post_edges = list(post_graph.derivatives())
        diff = list(set(post_edges) - set(pre_edges))
        self.assertEqual(len(diff), 0)
        for e in post_edges:
            if e.v.get_key() == source:
                self.assertEqual(e.confidence,pre_conf + self._tg.derivatives._standard_modifier)

        pre_graph = self._tg.derivatives.get(result,threshold=5)
        pre_edges = list(pre_graph.derivatives())
        try:
            pre_conf = [e.confidence for e in pre_edges if e.n.get_key() == result][0]
        except IndexError:
            pre_conf = 0

        self._handlers.feedback(source,result,positive=False)
        post_graph = self._tg.derivatives.get(result,threshold=5)
        post_edges = list(post_graph.derivatives())
        diff = list(set(post_edges) - set(pre_edges))
        self.assertEqual(len(diff), 0)
        for e in post_edges:
            if e.v.get_key() == source:
                self.assertEqual(e.confidence,pre_conf - self._tg.derivatives._standard_modifier)


class TestGraphQueryHandlerModule(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self._wg = WorldGraph(uri,db_auth)
        self._handlers = ModuleHandler(self._wg.truth)
        self._tg = self._wg.truth

    def test_module_query_direct_match(self):
        res = self._handlers.handle("Ptet")
        m_graph = self._tg.modules.get()
        modules = [str(m) for m in m_graph.modules()]
        for entity,data in res.items():
            for res in data:
                self.assertIn(res[1]["entity"],modules)

def make_random_changes(sequence, percentage):
    num_changes = int(len(sequence) * percentage / 100)
    seq_list = list(sequence)
    indices = random.sample(range(len(sequence)), num_changes)
    for index in indices:
        current_base = seq_list[index]
        new_base = random.choice('ACGT'.replace(current_base, ''))
        seq_list[index] = new_base
    modified_sequence = ''.join(seq_list)
    return modified_sequence