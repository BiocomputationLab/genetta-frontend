import os
from abc import ABCMeta, abstractmethod
import rdflib
from pathlib import Path

base_storage = os.path.join(os.path.dirname(__file__),"records")
db_threshold = 20 # Mb

class DatabaseInterface:
    __metaclass__ = ABCMeta
    def __init__(self,record_storage):
        self.record_storage = os.path.join(base_storage,record_storage)
        self.id_codes = []
        
    @abstractmethod
    def get(self,id):
        pass

    @abstractmethod
    def query(self,query_string):
        pass

    @abstractmethod
    def count(self,query_string):
        pass

    @abstractmethod
    def is_record(self,identity):
        pass
    
    @abstractmethod
    def sequence(self,sequence,similarity=None):
        pass
    
    @abstractmethod
    def get_uri(self,name):
        pass

    @abstractmethod
    def is_up(self):
        pass
    
    def cleanup(self):
        def get_file_size(file_path):
            return os.path.getsize(file_path)
        def get_dir_size(files):
            return (sum(f.stat().st_size for f in files if f.is_file()) 
                    / (1048576))
        path = Path(self.record_storage)
        files = sorted(list(path.glob('**/*')), key=get_file_size)
        ts = get_dir_size(files)
        nfr = 0
        while ts > db_threshold:
            file = files.pop()
            ts = get_dir_size(files)
            nfr += 1
            os.remove(file)
                

    def _load_graph(self,fn):
        record_graph = rdflib.Graph()
        record_graph.parse(fn)
        return record_graph
        
    def _store_record(self,target,record):
        try:
            os.makedirs(self.record_storage)
        except FileExistsError:
            pass
        
        if os.path.isfile(target):
            return target
        try:
            f = open(target,"a")
        except OSError:
            return None
        f.write(record)
        f.close()
        return target



