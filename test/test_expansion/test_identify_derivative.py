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
from app.tools.kg_expansion.expansions.identify_derivative import TruthDerivative
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

nv_synonym = str(model.identifiers.external.synonym)
nv_derivatives = str(model.identifiers.external.derivative)
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
    
    def test_identify_derivative_expansion(self):
        ppe = TruthDerivative(self.tg,data_miner)
        inp_res = "https://synbiohub.programmingbiology.org/public/Cello_Parts/pTet_synonym/1"
        props = {nv_seq:"TACTCCACCGTTGGCTTTTTTCCCTATCAGTGATAGAGATTGACATCCCTATCAGTGATAGAGATAATGAGCAC"}
        self.tg.add_node(inp_res,nv_promoter,**props)
        self.tg.derivatives.positive(inp_res,"https://synbiohub.org/public/igem/BBa_K1632004/1")
        self.tg.derivatives.positive("https://synbiohub.org/public/igem/BBa_K1913000/1",inp_res)
        pre_e = self.tg.edges()
        ppe.expand()
        post_e = self.tg.edges()

        diff = list(set(post_e) - set(pre_e))
        all_edges = list(set(post_e+pre_e))
        all_seqs = ([s.n.hasSequence for s in all_edges 
                     if hasattr(s.n,"hasSequence")] + 
                    [s.v.hasSequence for s in all_edges 
                     if hasattr(s.v,"hasSequence")])
        tn_in = False
        for edge in diff:
            if edge.get_type() == nv_synonym:
                self.assertEqual(edge.confidence,100)
                self.assertEqual(all_seqs.count(edge.n.hasSequence),1)
            elif edge.get_type() == nv_derivatives:
                score = int(aligner.sequence_match(edge.n.hasSequence,
                                                   edge.v.hasSequence)*100)
                self.assertEqual(score,edge.confidence)
            else:
                self.fail(edge.get_type())
            if inp_res == edge.v.get_key():
                tn_in = True
        
        if not tn_in:
            self.fail("No test synonym.")

        test_source = "https://synbiohub.programmingbiology.org/public/Cello_Parts/pTet1"
        self.tg.remove_node(inp_res)
        for i in range(0,20):
            self.tg.synonyms.negative(test_source,inp_res)

    