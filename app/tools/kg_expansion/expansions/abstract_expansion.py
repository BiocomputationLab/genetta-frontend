import re
from abc import ABC
from abc import abstractmethod

class AbstractExpansion(ABC):
    def __init__(self,truth_graph,miner,name=None):
        self._tg = truth_graph
        self._miner = miner
        self._match_threshold = 80
        if name is None:
            self.name = self.__class__.__name__
        else:
            self.name = name
    
    @abstractmethod
    def expand(self):
        pass
    
    def _add_related_node(self,graph,related,r_type):
        ppn = self._create_uri(related.get_key(),r_type)
        return graph.add_node(ppn,r_type)

    def _create_uri(self,original,i_type):
        it_name = self._get_name(i_type).lower()
        return f'{self._get_prefix(original)}_{it_name}/1'

    def _get_prefix(self,subject):
        split_subject = self._split(subject)
        if split_subject[-1].isdigit():
            return subject[:-2]
        else:
            return subject
    
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
