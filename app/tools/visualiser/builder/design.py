from app.tools.visualiser.builder.abstract import AbstractBuilder
from app.tools.visualiser.builder.builders.design.hierarchy import HierarchyViewBuilder
from app.tools.visualiser.builder.builders.design.interaction import InteractionViewBuilder
from app.tools.visualiser.builder.builders.design.interaction_explicit import InteractionExplicitViewBuilder
from app.tools.visualiser.builder.builders.design.interaction_genetic import InteractionGeneticViewBuilder
from app.tools.visualiser.builder.builders.design.interaction_protein import InteractionProteinViewBuilder
from app.tools.visualiser.builder.builders.design.interaction_verbose import InteractionVerboseViewBuilder
from app.tools.visualiser.builder.builders.design.interaction_io import InteractionIoViewBuilder
from app.tools.visualiser.builder.builders.design.pruned import PrunedViewBuilder
from app.tools.visualiser.builder.builders.design.position import PositionViewBuilder
from app.tools.visualiser.builder.builders.full import FullViewBuilder

predicates = {"Intersection":"ALL",
              "Union":"ANY",
              "Difference":"SINGLE"}

class DesignBuilder(AbstractBuilder):
    def __init__(self,graph):
        super().__init__(graph)
        self._dg = self._graph.get_design(None)
        self._view_builder = FullViewBuilder(self._dg)
        self._predicate = "ALL"
    
    def build(self,*args,**kwargs):
        super().build(*args,predicate=self._predicate,**kwargs)
        
    def set_full_view(self):
        self._view_builder = FullViewBuilder(self._dg)

    def set_pruned_view(self):
        self._view_builder = PrunedViewBuilder(self._dg)
         
    def set_hierarchy_view(self):
        self._view_builder = HierarchyViewBuilder(self._dg)

    def set_interaction_explicit_view(self):
        self._view_builder = InteractionExplicitViewBuilder(self._dg)

    def set_interaction_verbose_view(self):
        self._view_builder = InteractionVerboseViewBuilder(self._dg)

    def set_interaction_view(self):
        self._view_builder = InteractionViewBuilder(self._dg)

    def set_interaction_genetic_view(self):
        self._view_builder = InteractionGeneticViewBuilder(self._dg)

    def set_interaction_protein_view(self):
        self._view_builder = InteractionProteinViewBuilder(self._dg)

    def set_interaction_io_view(self):
        self._view_builder = InteractionIoViewBuilder(self._dg)

    
    def set_positional_view(self):
        self._view_builder = PositionViewBuilder(self._dg)
        
    def get_design_names(self):
        return self._graph.get_design_names()

    def get_loaded_design_names(self):
        return self._dg.name
    
    def get_load_predicates(self):
        return predicates.keys()

    def set_design_names(self,names,load_predicate):
        if load_predicate not in predicates:
            raise ValueError(f'{load_predicate} not valid load predicate, choices are: {str(predicates.keys())}')
        self.set_design(self._graph.get_design(names),predicates[load_predicate])
        
    def set_design(self,design,predicate):
        self._dg = design
        self._view_builder.set_graph(design)
        self._predicate = predicate

    def get_children(self,node):
        return self._dg.get_children(node)
    
    def get_parents(self,node):
        return self._dg.get_parents(node)

    def get_entity_depth(self,subject):
        return self._dg.get_entity_depth(subject)

    def get_root_entities(self):
        return self._dg.get_root_entities()
