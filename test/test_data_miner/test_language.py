import unittest
import sys,os
sys.path.insert(0, os.path.join("..","..","..",".."))
sys.path.insert(0, os.path.join("..","..",".."))
sys.path.insert(0, os.path.join("..",".."))
from app.tools.data_miner.language.analyser import LanguageAnalyser

class TestLanguageAnalyser(unittest.TestCase):

    def setUp(self):
        self.language_analyser = LanguageAnalyser()

    def tearDown(self):
        None

    def test_break_text(self):
        text = "ptet"
        res = self.language_analyser.break_text(text)
        self.assertEqual(res,[text])

        text = "ptet is a repressible promoter."
        res = self.language_analyser.break_text(text)
        self.assertEqual(res,[text])


        text = "ptet is a repressible promoter. ptet is repressed by the TetR protein"
        res = self.language_analyser.break_text(text)
        expected_text = ["ptet is a repressible promoter.", 
                         "ptet is repressed by the TetR protein"]
        self.assertEqual(res,expected_text)


        text = "ptet is a repressible promoter. ptet is repressed by the TetR protein.The"
        res = self.language_analyser.break_text(text)
        expected_text = ["ptet is a repressible promoter.", 
                         "ptet is repressed by the TetR protein.",
                         "The"]
        self.assertEqual(res,expected_text)

    def test_get_subject(self):
        text = "laci represses tetr"
        res = self.language_analyser.get_subject(text)
        self.assertEqual(res,"laci")

    def test_get_proper_nouns(self):
        text = "ptet laci repression Matthew"
        res = self.language_analyser.get_proper_nouns(text)
        self.assertEqual(res,["Matthew"])

    def test_get_nouns(self):
        text = "ptet laci repression Matthew"
        res = self.language_analyser.get_nouns(text)
        self.assertEqual(res,["ptet","laci","repression"])

    def test_get_all_nouns(self):
        text = "ptet laci repression Matthew or Kevin"
        res = self.language_analyser.get_all_nouns(text)
        self.assertEqual(res,["ptet","laci","repression","Matthew","Kevin"])

    def test_get_all_nouns_uri(self):
        text = "ptet laci https://synbiohub.programmingbiology.org/public/GokselEco1C1G1T2/pTet/1 Matthew or Kevin"
        res = self.language_analyser.get_all_nouns(text)
        print(res)
        self.assertEqual(res,["ptet","laci","https://synbiohub.programmingbiology.org/public/GokselEco1C1G1T2/pTet/1","Matthew","Kevin"])

if __name__ == '__main__':
    unittest.main()
