import unittest
import os
import sys
from rdflib import URIRef

sys.path.insert(0, os.path.join(".."))
sys.path.insert(0, os.path.join("..",".."))
sys.path.insert(0, os.path.join("..","..",".."))

from app.visualiser.builder.truth import TruthBuilder
from app.graph.world_graph import WorldGraph
from  app.graph.utility.model.model import model
from app.converter.sbol_convert import convert

curr_dir = os.path.dirname(os.path.realpath(__file__))
test_fn = os.path.join(curr_dir,"..","files","nor_full.xml")


class TestViews(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.wg = WorldGraph()
        self.builder = TruthBuilder(self.wg)

    def test_provenance(self):
        self.builder.set_provenance_view()
        self.builder.build()
        graph = self.builder.view
        view_edges = graph.edges()
        self.assertCountEqual(self.wg.truth.derivatives.get(),view_edges)

    def test_synonym(self):
        self.builder.set_synonym_view()
        self.builder.build()
        graph = self.builder.view
        view_edges = graph.edges()
        self.assertCountEqual(self.wg.truth.synonyms.get(),view_edges)
            

def diff(list1,list2):
    diff = []
    for n,v,e in list1:
        for n1,v1,e1 in list2:
            if n == n1 and v == v1 and e == e1:
                break
        else:
            diff.append((n,v,e,k))
    return diff


if __name__ == '__main__':
    unittest.main()
