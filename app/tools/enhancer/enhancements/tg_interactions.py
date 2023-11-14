from app.tools.enhancer.enhancements.abstract_enhancements import AbstractEnhancement
from app.graph.utility.model.model import model
from app.graph.utility.graph_objects.node import Node

class TruthInteractions(AbstractEnhancement):
    '''
    Extracts all entities from the truth graph 
    into the design graph (assumes canonical)
    '''
    def __init__(self, world_graph, miner):
        super().__init__(world_graph, miner)

    def enhance(self,graph_name,automated=False):
        '''
        Considerations:
        1. What if an interaction that is pulled in, the two 
        graphs (DG and TG) dont have the same number of participants? 
        That is, the DG's parts dont all refer to canonical entities? Its true 
        that even during canonicalisation, 
        an entity may not be from the TG. I guess I need to think if this is the 
        role of this function or something to be handled in the canonicaliser.
        '''
        changes = {}
        graph = self._wg.get_design(graph_name)
        d_entities = graph.get_physicalentity()
        ti_graph = self._wg.truth.interactions.get()
        seen_ints = []
        for e in d_entities:
            d_ints = self._existing_interactions(e,graph)
            for t_i in ti_graph.interactions(participant=e.get_key()):
                if t_i in seen_ints:
                    continue
                seen_ints.append(t_i)
                t_i_ps = list(ti_graph.interactions(interaction=t_i))
                if self._does_exist(d_ints,t_i,t_i_ps):
                    continue
                if automated:
                    changes.update(self.apply({e:t_i},graph_name))
                    continue
                
                comment = (f'{t_i.name} - Participants: ' +
                f'{", ".join([f"{i.v.name}-{i.name}" for i in  t_i_ps])}')
                confidence = t_i_ps[0].confidence
                changes= self._potential_change(changes,e,t_i,
                                                confidence,comment)
        return changes
    
    def apply(self,replacements,graph_name):
        changes = {}
        graph = self._wg.get_design(graph_name)
        ti_graph = self._wg.truth.interactions.get()
        for subj,inter in replacements.items():
            if not isinstance(inter,(tuple,list,set)):
                inter = [inter]
            for i in inter:
                if not isinstance(i,Node):
                    i = ti_graph.get_node(i)
                d_inter = i.duplicate(graph.name)
                t_i_parts = ti_graph.interactions(interaction=i)
                parts = []
                for t_i_p in t_i_parts:
                    part = t_i_p.v.duplicate(graph.name)
                    #if not t_i_p.v.is_in(d_entities):
                    #    pass
                    parts.append((part,t_i_p.get_type()))
                new_edges = self._add_interaction(graph,d_inter,parts)
                changes[subj] = self._define_change(new_edges)
        return changes



    def _existing_interactions(self,entity,graph):
        ints = list(set([k.n for k in graph.get_interactions(entity)]))
        int_struct = []
        for i in ints:
            parts = [(p.v.get_key(),p.get_type()) for p 
                     in graph.get_interaction_elements(i)]
            int_struct.append((i.get_type(),parts))
        return int_struct
    

    def _does_exist(self,existing,inter,parts):
        for e_int,e_parts in existing:
            if e_int != inter.get_type():
                continue
            parts = [(p.v.get_key(),p.get_type()) for p in parts]
            if set(e_parts) == set(parts):
                return True
        return False 