import re
from abc import ABC
from app.graph.utility.graph_objects.edge import Edge
from app.graph.utility.graph_objects.node import Node
class AbstractEnhancement(ABC):
    def __init__(self,world_graph,miner):
        self._wg = world_graph
        self._miner = miner
        self.name = self.__class__.__name__
                
    def _add_interaction(self,graph,interaction,entities):
        edges = []
        graph.add_node(interaction.get_key(),interaction.get_type(),
                       **interaction.properties)
        for e,i_type in entities:
            graph.add_node(e.get_key(),e.get_type(),**e.properties)
            edges.append((interaction,e,i_type))
        graph.add_edges(edges)
        return edges
    
    def _define_change(self,edges):
        changes = []
        for edge in edges:
            if isinstance(edge,Edge):
                changes.append(f'{edge.n.name} - {edge.name} - {edge.v.name}')
            else:
                changes.append(f'{self._get_name(edge[0])} - ' + 
                               f'{self._get_name(edge[2])} - ' +                          
                               f'{self._get_name(edge[1])}')
        return changes

    def _add_related_node(self,graph,related,r_type):
        ppn = self._create_uri(related.get_key(),r_type)
        return graph.add_node(ppn,r_type)

    def _create_uri(self,original,i_type):
        it_name = self._get_name(i_type).lower()
        return f'{self._get_prefix(original)}_{it_name}/1'

    def _potential_change(self,cur_changes,subject,option,score,
                          comment):
        i_dict = {"score" : score,
                  "comment" : comment}
        subject = str(subject)
        option = str(option)
        if subject in cur_changes:
            cur_changes[subject][option] = i_dict
        else:
            cur_changes[subject] = {option : i_dict} 
        return cur_changes

    def _get_prefix(self,subject):
        split_subject = _split(subject)
        if split_subject[-1].isdigit():
            return subject[:-2]
        else:
            return subject

    def _get_name(self,subject):
        if isinstance(subject,Node):
            return subject.name
        split_subject = _split(subject)
        if len(split_subject[-1]) == 1 and split_subject[-1].isdigit():
            return split_subject[-2]
        elif len(split_subject[-1]) == 3 and _isfloat(split_subject[-1]):
            return split_subject[-2]
        else:
            return split_subject[-1]


def _split(uri):
    return re.split('#|\/|:', uri)


def _isfloat(x):
    try:
        float(x)
        return True
    except ValueError:
        return False
