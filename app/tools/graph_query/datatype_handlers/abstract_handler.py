from abc import ABC, abstractmethod
import re
from app.tools.data_miner.data_miner import data_miner
from app.graph.utility.model.model import model

o_synonym = str(model.identifiers.objects.synonym)

class AbstractHandler(ABC):
    def __init__(self,graph):
        self._graph = graph
        self._miner = data_miner

    def get_name(self):
        return self.__class__.__name__
    
    @abstractmethod
    def get_description(self):
        pass

    @abstractmethod
    def get_example(self):
        pass

    @abstractmethod
    def handle(self,query,strict=False):
        pass

    @abstractmethod
    def feedback(self, source, result, positive=True):
        pass

    def _identify_entities(self,qry_elements,viewgraph=None,index=None,
                           predicate=None,threshold=None,strict=False):
        entities = {}
        if not isinstance(qry_elements,list):
            qry_elements = [qry_elements]
        qry_strs = []
        for qry_str in qry_elements:
            if self.is_url(qry_str):
                continue
            qry_strs.append(qry_str)
            split = [e for e in re.split("[-_]", qry_str) if e != ""]
            if len(split) > 1:
                qry_strs += split

        qry_uris = [q for q in qry_elements if self.is_url(q)]
        if len(qry_strs) > 0:
            if not strict:
                if index is None:
                    index = {"name":qry_strs}
                else:
                    if not isinstance(index,list):
                        index = [index]
                    index = {ti:qry_strs for ti in index}
                qti = self._graph.query_text_index(index,
                                                predicate=predicate,
                                                fuzzy=True,
                                                threshold=threshold)
                entities.update(qti)
            else:
                for q in qry_strs:
                    for res in self._graph.node_query(name=q):
                        entities[res] = 100
        for qry_uri in qry_uris:
            if viewgraph is not None:
                entity = viewgraph.get_node(qry_uri)
                if entity is not None:
                    entities[entity] = 100
            else:
                es = {i:100 for i in self._graph.node_query(qry_uri)}
                entities.update(es)
        return entities
    
    def _merge_duplicates(self,list1,list2):
        final_list = list2.copy()
        for l in list1:
            if l[1]["entity"] in [l2[1]["entity"] for l2 in  list2]:
                continue
            final_list.append(l)
        return final_list
    
    def _cast_synonyms(self,entities,viewgraph):
        for entity in entities:
            if entity.get_type() == o_synonym:
                for e in viewgraph.synonyms(synonym=entity):
                    yield e.n
            else:
                yield entity

    def _rank_result(self,results):
        try:
            results = list(set(results))
        except TypeError:
            pass
        results.sort(key=lambda x: x[0], reverse=True)
        return results
    
    def is_url(self,string):
        # Regular expression pattern for URL matching
        url_pattern = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return re.match(url_pattern, string) is not None
    
    def _get_name(self,subject):
        split_subject = self._split(subject)
        if len(split_subject[-1]) == 1 and split_subject[-1].isdigit():
            return split_subject[-2]
        elif len(split_subject[-1]) == 3 and self._isfloat(split_subject[-1]):
            return split_subject[-2]
        else:
            return split_subject[-1]


    def _split(self,uri):
        return re.split('#|\/|:', uri)


    def _isfloat(self,x):
        try:
            float(x)
            return True
        except ValueError:
            return False