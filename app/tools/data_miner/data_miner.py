from app.tools.data_miner.language.analyser import LanguageAnalyser
from app.tools.data_miner.database.handler import DatabaseHandler
from app.tools.data_miner.ontology.handler import OntologyHandler
from app.tools.data_miner.graph_analyser.analyser import GraphAnalyser
from app.tools.data_miner.utility.identifiers import identifiers
from rdflib import RDF
s_cd = identifiers.objects.component_definition

class DataMiner:
    '''
    Acts as a facade interface for several utlity tools.
    '''
    def __init__(self):
        self._database = DatabaseHandler()
        self._language = LanguageAnalyser()
        self._ontology = OntologyHandler()
        self._graph_analyser = GraphAnalyser(self._database)

    # -- Database --
    def is_reference(self,uri):
        return self._database.is_record(uri)

    def get(self,name,timeout=10,db_name=None):
        return self._database.get(name,timeout=timeout,db_name=db_name)
    
    def query(self,query,lazy=False):
        return self._database.query(query,lazy=lazy)

    def get_igem(self,out_fn):
        return self._database.download_igem_parts(out_fn)
    
    def get_vpr(self,out_fn):
        return self._database.get_vpr_data(out_fn)
    
    def sequence_match(self,sequence,db_name=None):
        s = sequence.replace("\n", "").replace("\t", "").replace(" ", "")
        matches = self._database.sequence_search(s,db_name=db_name)
        if matches is None:
            return None
        if len(matches) == 1:
            return list(matches.keys())[0]
        # When a part has multiple names of 
        # is referenced in multiple records.
        cds = []
        for uri,match in matches.items():
            r = self._database.get(uri)
            cds += r.triples((None,RDF.type,s_cd))
        return str(max(set(cds), key=cds.count)[0])
    
    # -- Language --
    def break_text(self,text):
        return self._language.break_text(text)
    
    def get_subject(self,sentence):
        return self._language.get_subject(sentence)

    def get_entities(self,text):
        results = self._language.get_non_stop_words(text)
        #results = self._language.get_all_uris(text)
        #results += self._language.get_all_nouns(text)   
        return list(set(results))
    
    def word_similarity(self,word,words):
        for w in words:
            yield self._language.similarity(word,w)
        
    # -- Ontology -- 

    # -- Graph analyser --     
    def record_to_node(self,graph,key=None,fragments=[]):
        return self._graph_analyser.graph_to_node(graph,key,fragments)
    
    def get_graph_subject(self,graph,fragments=None):
        return self._graph_analyser.get_subject(graph,fragments)
    
data_miner = DataMiner()
