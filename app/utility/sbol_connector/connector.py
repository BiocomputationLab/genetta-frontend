
import os
from rdflib import URIRef,Graph
from requests.exceptions import ConnectionError
from app.utility.sbol_connector.sbol_identifiers import identifiers
from app.utility.sbol_connector.interfaces.lcphub_interface import LCPHubInterface
from app.utility.sbol_connector.interfaces.sevahub_interface import SevaHubInterface
from app.utility.sbol_connector.interfaces.synbiohub_interface import SynBioHubInterface
from app.utility.sbol_connector.graph_wrappers.sbol import SBOLGraph

prune_predicates = [identifiers.predicates.was_generated_by,
                    identifiers.predicates.created,
                    identifiers.predicates.toplevel,
                    identifiers.predicates.ownedby]

prune_objects = [identifiers.objects.model,
                identifiers.objects.collection,
                identifiers.objects.attachment,
                identifiers.objects.implementation,
                identifiers.objects.experiment,
                identifiers.objects.experimental_data,
                identifiers.objects.usage,
                identifiers.objects.activity,
                identifiers.objects.association,
                identifiers.objects.agent,
                identifiers.objects.plan]

class SBOLConnector:
    def __init__(self):
        self.hubs = {"lcp"   :  LCPHubInterface(),
                    "seva"   : SevaHubInterface(),
                    "synbio" :SynBioHubInterface()}
    

    def query(self,query,search_limit=5,hubs=[]):
        if hubs == []:
            hubs = list(self.hubs.values())
        else:
            hubs = [self.hubs[hub] for hub in hubs]
        results = []
        for hub in hubs:
            results += hub.query(query,search_limit=search_limit)
        return results

    def get(self,identifier,output=None):
        for hub in self.hubs.values():
            if os.path.commonprefix([hub.base,identifier]) == hub.base:
                ret_val = self._handle_get(identifier,hub,output)
                if ret_val is not None:
                    return ret_val
        else:
            for hub in self.hubs.values():
                try:
                    ret_val = self._handle_get(identifier,hub,output)
                    if ret_val is not None:
                        return ret_val
                except ValueError:
                    continue

        raise ValueError(f'{identifier} is unknown to hubs.')
    
    def prune(self,graph,predicates=None,objects=None):
        if isinstance(graph,str):
            graph = SBOLGraph(graph)

        subjects = []
        if predicates == []:
            predicates = prune_predicates
        elif predicates is None:
            predicates = []
        else:
            predicates = [URIRef(p) for p in predicates]

        if objects == []:
            objects = prune_objects
        elif objects is None:
            objects = []
        else:
            objects = [URIRef(o) for o in objects]

        for s,p,o in graph:
            if o in objects:
                subjects.append(s)        
        for s,p,o in graph:
            if s in subjects:
                graph.remove((s,p,o))
            elif o in subjects:
                graph.remove((s,p,o))
            elif o in objects:
                graph.remove((s,p,o))
            elif p in predicates:
                graph.remove((s,p,o))
        return graph

    def connect(self,graph):
        if isinstance(graph,str):
            graph = SBOLGraph(graph)

        definitions = graph.get_definitions()
        for s,p,o in definitions:
            definition = graph.get_rdf_type(o)
            if definition is not None:
                continue
            try:
                sub_graph = self.get(o)
            except ValueError:
                continue
            graph.add_graph(sub_graph)
        return graph

    def can_connect(self,filename):
        try:
            graph = SBOLGraph(filename)
        except Exception as ex:
            return False
        definitions = graph.get_definitions()
        for s,p,o in definitions:
            definition = graph.get_rdf_type(o)
            if definition is None:
                return True
        return False

    def split(self,filename,gn):
        try:
            graph = SBOLGraph(filename)
        except Exception as ex:
            return [(filename,gn)]

        graphs = []
        for collect in graph.get_collections():
            c_name = graph.get_name(collect)
            col_gn = f'{gn}-{c_name}'
            for member in graph.get_members(collect):
                member_type = graph.get_rdf_type(member)
                if member_type == identifiers.objects.component_definition:
                    s_trips = graph.subgraph(member)
                    sub_graph = Graph()
                    [sub_graph.add(trip) for trip in s_trips]
                    new_gn = f'{col_gn}-{graph.get_name(member)}'
                    new_fn = f'{os.path.split(filename)[0]}{os.path.sep}{new_gn}.xml'
                    sub_graph.serialize(new_fn,"xml") 
                    graphs.append((new_fn,new_gn))
        if len(graphs) == 0:
            return [(filename,gn)]

        return graphs
    
    def _handle_get(self,identifier,hub,output):
        try:
            graph = hub.get(identifier,output)
        except ConnectionError:
            return None
        if graph is not None:
            return SBOLGraph(graph)
        return None