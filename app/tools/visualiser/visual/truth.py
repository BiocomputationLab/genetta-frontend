import dash_cytoscape as cyto
cyto.load_extra_layouts()
from app.tools.visualiser.visual.abstract_design import AbstractDesignVisual
from app.tools.visualiser.builder.truth import TruthBuilder
from app.tools.visualiser.visual.handlers.truth.color import TruthColorHandler

class TruthVisual(AbstractDesignVisual):
    def __init__(self,graph):
        super().__init__(TruthBuilder(graph))
        self._color_h = TruthColorHandler(self._builder)
            
    # ---------------------- Preset ------------------------------------
    def set_provenance_preset(self):
        '''
        Pre-set methods with an affinity for displaying the provenance view.
        '''
        preset_functions = [self.set_network_mode,
                            self.set_provenance_view,
                            self.set_cose_layout,
                            self.add_type_node_color,
                            self.add_type_edge_color,
                            #self.add_node_name_labels, 
                            self.add_edge_no_labels,
                            self.add_standard_node_size,
                            self.set_circle_node_shape,
                            self.set_bezier_edge_shape]
        return self._set_preset(preset_functions)
    
    def set_synonym_preset(self):
        '''
        Pre-set methods with an affinity for displaying the synonym view.
        '''
        preset_functions = [self.set_network_mode,
                            self.set_synonym_view,
                            self.set_cose_layout,
                            self.add_type_node_color,
                            self.add_standard_edge_color,
                            self.add_node_name_labels, 
                            self.add_edge_no_labels,
                            self.add_standard_node_size,
                            self.set_circle_node_shape,
                            self.set_bezier_edge_shape]
        return self._set_preset(preset_functions)
    
    def set_hierarchy_preset(self):
        '''
        Pre-set methods with an affinity for displaying the hierarchy view.
        '''
        preset_functions = [self.set_tree_mode,
                            self.set_hierarchy_view,
                            self.set_dagre_layout,
                            self.add_hierarchy_node_color,
                            self.add_hierarchy_edge_color,
                            self.add_node_name_labels, 
                            self.add_edge_no_labels,
                            self.add_hierarchy_node_size,
                            self.set_circle_node_shape,
                            self.set_bezier_edge_shape]
        return self._set_preset(preset_functions)

    def set_prune_preset(self):
        '''
        Pre-set methods with an affinity for displaying the pruned graph view.
        '''
        preset_functions = [self.set_network_mode,
                            self.set_pruned_view,
                            self.set_cose_layout,
                            self.add_type_node_color, 
                            self.add_type_edge_color,
                            #self.add_node_name_labels,
                            self.add_edge_no_labels,
                            self.add_centrality_node_size,
                            self.set_circle_node_shape,
                            self.set_bezier_edge_shape]
        return self._set_preset(preset_functions)

    def set_interaction_level_0_explicit_preset(self):
        '''
        Pre-set methods with an affinity for displaying the explicit interaction view.
        '''
        preset_functions = [self.set_network_mode,
                            self.set_interaction_explicit_view,
                            self.set_dagre_layout,
                            self.add_role_node_color,
                            self.add_type_edge_color,
                            self.add_edge_no_labels,
                            self.add_node_name_labels,
                            self.add_standard_node_size,
                            self.set_circle_node_shape,
                            self.set_bezier_edge_shape]
        return self._set_preset(preset_functions)

    def set_interaction_level_1_verbose_preset(self):
        '''
        Pre-set methods with an affinity for displaying the verbose interaction view.
        '''
        preset_functions = [self.set_network_mode,
                            self.set_interaction_verbose_view,
                            self.set_dagre_layout,
                            self.add_role_node_color,
                            self.add_type_edge_color,
                            self.add_edge_no_labels,
                            self.add_node_name_labels,
                            self.add_standard_node_size,
                            self.set_circle_node_shape,
                            self.set_bezier_edge_shape]
        return self._set_preset(preset_functions)

    def set_interaction_level_2_standard_preset(self):
        '''
        Pre-set methods with an affinity for displaying the interaction view.
        '''
        preset_functions = [self.set_network_mode,
                            self.set_interaction_view,
                            self.set_dagre_layout,
                            self.add_role_node_color,
                            self.add_type_edge_color,
                            self.add_edge_no_labels,
                            self.add_node_name_labels,
                            self.add_standard_node_size,
                            self.set_circle_node_shape,
                            self.set_bezier_edge_shape]
        return self._set_preset(preset_functions)

    def set_interaction_level_3_genetic_preset(self):
        '''
        Pre-set methods with an affinity for displaying the genetic interaction view.
        '''
        preset_functions = [self.set_network_mode,
                            self.set_interaction_genetic_view,
                            self.set_dagre_layout,
                            self.add_type_node_color,
                            self.add_type_edge_color,   
                            self.add_edge_no_labels,
                            self.add_node_name_labels,
                            self.add_standard_node_size,
                            self.set_circle_node_shape,
                            self.set_bezier_edge_shape]
        return self._set_preset(preset_functions)

    def set_interaction_level_4_protein_preset(self):
        '''
        Pre-set methods with an affinity for displaying the ppi interaction view.
        '''
        preset_functions = [self.set_network_mode,
                            self.set_interaction_protein_view,
                            self.set_dagre_layout,
                            self.add_type_edge_color,
                            self.add_type_node_color,
                            self.add_node_name_labels,
                            self.add_edge_no_labels,
                            self.add_standard_node_size,
                            self.set_circle_node_shape,
                            self.set_bezier_edge_shape]
        return self._set_preset(preset_functions)

    def set_interaction_level_5_io_preset(self):
        '''
        Pre-set methods with an affinity for displaying the ppi interaction view.
        '''
        preset_functions = [self.set_network_mode,
                            self.set_interaction_io_view,
                            self.set_dagre_layout,
                            self.add_type_edge_color,
                            self.add_standard_node_color,
                            self.add_node_name_labels,
                            self.add_edge_no_labels,
                            self.add_standard_node_size,
                            self.set_circle_node_shape,
                            self.set_bezier_edge_shape]
        return self._set_preset(preset_functions)
    
    def set_provenance_view(self):
        '''
        Sub graph viewing only the provenances edges, 
        displaying parts which have a level of sequence similarity.
        '''
        if self.view == self.set_provenance_view:
            self._builder.set_provenance_view()
        else:
           self.view =self.set_provenance_view

    def set_synonym_view(self):
        '''
        Sub graph viewing only the synonym edges, 
        displaying parts which have multiple URI's.
        '''
        if self.view == self.set_synonym_view:
            self._builder.set_synonym_view()
        else:
           self.view =self.set_synonym_view

    def set_interaction_explicit_view(self):
        '''
        Sub graph viewing all consituent reactions of each interaction. 
        '''
        if self.view == self.set_interaction_explicit_view:
            self._builder.set_interaction_explicit_view()
        else:
           self.view =self.set_interaction_explicit_view

    def set_interaction_io_view(self):
        '''
        Sub graph viewing inputs and outputs of interaction network only.
        '''
        if self.view == self.set_interaction_io_view:
            self._builder.set_interaction_io_view()
        else:
           self.view =self.set_interaction_io_view
           
    def add_confidence_edge_color(self):
        '''
        Confidence is mapped to a color.
        '''
        if self.edge_color == self.add_confidence_edge_color:
            return self._color_h.edge.confidence()
        else:
            self.edge_color = self.add_confidence_edge_color