import time
from urllib.error import HTTPError as uHTTPerror
from requests.exceptions import HTTPError as rHTTPError
from requests.exceptions import ConnectionError, ReadTimeout

from app.tools.data_miner.database.interfaces import hub_interface
from app.tools.data_miner.database.interfaces.genbank_interface import GenBankInterface

class DatabaseUtility:
    def __init__(self):
        self.db_mapping_calls = {"synbiohub" : hub_interface.SynBioHubInterface(),
                                 "lcp"       : hub_interface.LCPHubInterface(),
                                 "sevahub"   : hub_interface.SevaHubInterface(),
                                 "genbank"   : GenBankInterface()}

    def get(self,id,db_name,timeout=10):
        attempts = 0
        if not self.db_mapping_calls[db_name].is_up():
            print(f'WARN: {db_name} is down for get.')
            return None
        while attempts < 5:
            try:
                return self.db_mapping_calls[db_name].get(id,timeout=timeout)
            except rHTTPError:
                attempts = attempts + 1
                time.sleep(2)
            except (uHTTPerror,ValueError,KeyError):
                return None
    
    def count(self,query,db_name):
        if not self.db_mapping_calls[db_name].is_up():
            print(f'WARN: {db_name} is down for count.')
            return 0
        return self.db_mapping_calls[db_name].count(query)

    def query(self,query,db_name,limit = 5):
        attempts = 0
        if not self.db_mapping_calls[db_name].is_up():
            print(f'WARN: {db_name} is down for query.')
            return []
        while attempts < 5:
            try:
                return self.db_mapping_calls[db_name].query(query,limit=limit)
            except (uHTTPerror,rHTTPError,ConnectionError,ReadTimeout):
                print(f'WARN:: Err querying with {query} for db: {db_name}. Attempt: {attempts}')
                attempts = attempts + 1
                time.sleep(5)
        return []

    def is_record(self,identity,db_name):
        db = self.db_mapping_calls[db_name]
        if not self.db_mapping_calls[db_name].is_up():
            print(f'WARN: {db_name} is down for is record.')
            return False
        if not hasattr(db,"base") or db.base not in identity:
            return False
        return db.is_triple(s=identity)

    def get_uri(self,name,db_name):
        if not self.db_mapping_calls[db_name].is_up():
            print(f'WARN: {db_name} is down for get uri.')
            return False
        return self.db_mapping_calls[db_name].get_uri(name)

    def sequence(self,sequence,db_name,similarity=None):
        attempts = 0
        db = self.db_mapping_calls[db_name]
        if not db.is_up():
            print(f'WARN: {db_name} is down for sequence search.')
            return None
        while attempts < 5:
            try:
                return db.sequence(sequence,similarity=similarity)
            except (uHTTPerror,rHTTPError,ConnectionError,ReadTimeout) as ex:
                print(f'WARN:: Err sequence search with {sequence} for db: {db_name}. Attempt: {attempts}')
                attempts += 1
                time.sleep(5)
        return None

    def get_metadata_identifiers(self):
        return [identity for db in self.db_mapping_calls.values() 
                         for identity in db.get_metadata_identifiers()]
         
    def get_potential_db_names(self,identity):
        potential_dbs = []
        for name,db in self.db_mapping_calls.items():
            if any(code.lower() in identity.lower() for code in db.id_codes):
                potential_dbs.append(name)
        return potential_dbs

    def cleanup(self,db_name):
        self.db_mapping_calls[db_name].cleanup()



        




