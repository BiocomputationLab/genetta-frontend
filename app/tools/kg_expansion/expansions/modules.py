import copy
from app.tools.kg_expansion.expansions.abstract_expansion import AbstractExpansion
from app.graph.utility.model.model import model

nv_interaction = model.identifiers.objects.interaction
nv_interaction_cc = model.get_class_code(nv_interaction)

nv_pe = model.identifiers.objects.physicalentity
nv_pe_cc = model.get_class_code(nv_pe)
nv_has_interaction = model.identifiers.predicates.hasInteraction

bl_types = [str(model.identifiers.objects.degradation),
            str(model.identifiers.objects.genetic_production)]

class TruthModules(AbstractExpansion):
    def __init__(self, truth_graph, miner):
        super().__init__(truth_graph, miner)

    def expand(self):        
        '''
        Creates new modules from interaction 
        components within the WKG.
        '''
        p_name = "TruthModule_in"
        try:
            self._tg.project.drop(p_name)
        except ValueError:
            pass
        self._tg.project.interaction(p_name)
        m_graph = self._tg.modules.get()
        e_modules = [s.get_key() for s in m_graph.modules()]
        inputs = self._tg.procedure.get_inputs(p_name)
        outputs = self._tg.procedure.get_outputs(p_name)    
        d_comps = self._tg.derivatives.get_components()
        for component in self._tg.procedure.get_components(p_name):
            # Decide using labels if its worth making a module.
            if not self._is_module(component):
                continue
            c_io = []
            for entity in component:
                if entity in inputs:
                    c_io = self._input(entity,d_comps,c_io)
            for entity in component:
                if entity in outputs:
                    c_io = self._output(entity,d_comps,c_io)
            seen_paths = {}
            for inps,outs in c_io:
                ints = []
                # Keep track just to create name
                path_outs = []
                for inp in inps:
                    for out in outs:
                        if inp in seen_paths and out in seen_paths[inp]:
                            paths = seen_paths[inp][out]
                        else:
                            paths = self._tg.procedure.dijkstra_sp(p_name,
                                                                    inp,
                                                                    out)
                            paths = [p["path"] for p in paths]
                            if inp not in seen_paths:
                                seen_paths[inp] = {}
                            seen_paths[inp][out] = paths
                        for path in paths:
                            ints += [e for e in path if 
                                    model.is_derived(e.get_type(),
                                                    nv_interaction_cc)]
                            if path[-2:] not in path_outs:
                                path_outs.append(path[-2:])
                ints = list(set(ints))
                module = self._generate_module_name(path_outs,e_modules)

                if self._does_exist(module,ints,e_modules,m_graph):
                    continue
                e_modules.append(module)
                for interaction in ints:
                    self._tg.modules.positive(module,interaction,
                                                nv_has_interaction)

    def _is_module(self,component):
        # Components with 1 interaction, dont use.
        interactions = [c for c in component if 
                        model.is_derived(c.get_type(),
                                         nv_interaction_cc)]
        if len(interactions) < 2:
            return False
        # Components which aren't module worthy 
        # (Genetic production & Degradation for example)
        if len([c for c in interactions if 
                c.get_type() not in bl_types]) == 0:
               return False
        return True
    
    def _generate_module_name(self,path_outs,e_modules):
        name = ""
        for interaction,entity in path_outs:
            name += f'/{entity.name}_{self._get_name(interaction.get_type())}'
        index = 1
        f_name = name
        while f_name in e_modules:
            f_name = f'{name}/{index}'
            index += 1
        return f_name
    
    def _does_exist(self,module,interactions,e_modules,m_graph):
        if module in e_modules:
            return True
        for module in m_graph.modules():
            e_ints = [e.v for e in m_graph.modules(module)]
            if len(list(set(interactions) & set(e_ints))) != 0:
                return True
        return False

    def _input(self,entity,d_comps,current):
        for comp in d_comps:
            if entity not in comp:
                continue
            for index,curr in enumerate(current):
                if any(item in curr for item in comp):
                    current[index][0].append(entity)
                    return current 
        current.append([[entity],[]])
        return current
    
    def _output(self,entity,d_comps,current):
        s_index = len(current)
        for index in range(0,s_index):
            for comp in d_comps:
                if entity not in comp:
                    continue
                if any(item in comp for item in current[index][1]):
                    duplicate = copy.copy(current[index])
                    duplicate[1] = [d for d in duplicate[1] if d not in comp]
                    duplicate[1].append(entity)
                    current.append(duplicate)
                    return current
            else:
                current[index][1].append(entity)
        return current