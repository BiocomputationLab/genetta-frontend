from app.tools.enhancer.enhancements.abstract_enhancements import AbstractEnhancement
from app.graph.utility.model.model import model
from app.graph.utility.graph_objects.node import Node

nv_promoter = str(model.identifiers.objects.promoter)
nv_cds = str(model.identifiers.objects.cds)
nv_terminator = str(model.identifiers.objects.terminator)
nv_activation = model.identifiers.objects.activation
nv_activator = model.identifiers.predicates.activator
nv_activated = model.identifiers.predicates.activated
class Positional(AbstractEnhancement):
    '''
    Introduces interactions based on the 
    position of entities on the sequence
    '''
    def __init__(self, world_graph, miner):
        super().__init__(world_graph, miner)


    def enhance(self,graph_name,automated=False):
        changes = {}
        graph = self._wg.get_design(graph_name)
        for path in graph.position_walk():
            c_prom_act = []
            for position in path:
                posof = graph.get_positionof(position,predicate="ANY")
                assert(len(posof) == 1)
                posof = posof[0].v
                if posof.get_type() == nv_promoter:
                    c_prom_act.append(posof)
                elif posof.get_type() == nv_cds and len(c_prom_act) > 0:
                    for prom in c_prom_act:
                        ex_ints = self._existing_interactions(prom,graph)
                        if len(ex_ints) != 0:
                            if self._does_exist(ex_ints,prom,posof):
                                continue
                        if automated:
                            changes.update(self.apply({prom:posof},
                                                    graph_name))
                            continue
                        comment = f'{prom.name} Activates {posof.name}'
                        confidence = 100
                        changes= self._potential_change(changes,prom,posof,
                                                        confidence,comment)
                elif posof.get_type() == nv_terminator:
                    c_prom_act = []
        return changes
    
    def apply(self,replacements,graph_name):
        changes = {}
        graph = self._wg.get_design(graph_name)
        for prom,cds in replacements.items():
            if not isinstance(cds,(list,tuple,set)):
                cds = [cds]
            for cd in cds:
                prom = graph.nodes(prom,predicate="ANY")[0]
                cd = graph.nodes(cd,predicate="ANY")[0]
                inter = (f'{self._get_prefix(prom.get_key())}'+
                        f'_activates_{self._get_name(cd.get_key())}')
                inter = graph.add_node(inter,nv_activation)
                parts = [(prom,nv_activator),
                        (cd,nv_activated)]
                new_edges = self._add_interaction(graph,inter,parts)
                if prom in changes:
                    changes[prom].append(self._define_change(new_edges))
                else:
                    changes[prom] = [self._define_change(new_edges)]
        return changes
    

    def _existing_interactions(self,entity,graph):
        ints = list(set([k.n for k in 
                         graph.get_interactions(entity,
                                                predicate="ANY")]))
        int_struct = []
        for i in ints:
            parts = [(p.v.get_key(),p.get_type()) for p 
                     in graph.get_interaction_elements(i,predicate="ANY")]
            int_struct.append((i.get_type(),parts))
        return int_struct
    

    def _does_exist(self,existing,prom,cds):
        for e_int,e_parts in existing:
            if e_int != str(nv_activation):
                continue
            if (prom.get_key(),str(nv_activator)) not in e_parts:
                continue
            if (cds.get_key(),str(nv_activated)) not in e_parts:
                continue
            return True
        return False 