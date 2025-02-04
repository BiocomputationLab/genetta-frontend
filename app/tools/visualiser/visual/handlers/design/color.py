import re
from app.tools.visualiser.visual.handlers.abstract_color import AbstractNodeColorHandler
from app.tools.visualiser.visual.handlers.abstract_color import AbstractEdgeColorHandler
from  app.graph.utility.model.model import model

class ColorHandler():
    def __init__(self,builder):
        self.node = NodeColorHandler(builder)
        self.edge = EdgeColorHandler(builder)

class NodeColorHandler(AbstractNodeColorHandler):
    def __init__(self,builder):
        super().__init__(builder)

    def role(self):
        '''
        Overview:
        The first layer of non-abstract classes 
        (Reaction,Interaction,DNA etc) are given a color.
        Each derived class within the design is given a 
        shade of that color.
        Why this looks so complicated is because we need 
        to find the last shade of that color used.
        '''
        colors = []
        col_map = {None : {"No_Role" : self._color_picker[0]}}
        shade_map = {}
        col_index = len(col_map)

        pe_id = model.identifiers.objects.physical_entity
        c_id = model.identifiers.objects.conceptual_entity
        pe_code = model.get_class_code(pe_id)
        c_code = model.get_class_code(c_id)
        pe_derived = [str(d[1]["key"]) for d in model.get_child_classes([pe_code,c_code])]
        for d in pe_derived:
            name = _get_name(d)
            col_map[name] = self._color_picker[col_index]
            col_index += 1

        for n in self._builder.v_nodes():
            n_type = n.get_type()
            if n_type == "None":
                colors.append(col_map[None])
                continue
            name = _get_name(n_type)
            if name not in col_map.keys():
                n_t_code = model.get_class_code(n_type)
                for b in [str(i[1]["key"]) for i in model.get_bases(n_t_code)]:
                    if b in pe_derived:
                        base = b
                        p_col = col_map[_get_name(b)]
                        break
                else:
                    colors.append(col_map[None])
                    continue
                if base not in shade_map.keys():
                    shade_map[base] = p_col
                p_col = shade_map[base]
                shade = self._color_picker.increase_shade(p_col)
                shade_map[base] = shade
                col_map[name] = shade
            colors.append({name : col_map[name]})
        return colors

    def hierarchy(self):
        colors = []
        colors_map = _init_hierarchy_map(self)
        for node in self._builder.v_nodes():
            if node not in colors_map.keys():
                for o in self._builder.in_edges(node):
                    o = o.n
                    if o in colors_map.keys():
                        color,depth = colors_map[o]
                        colors.append({depth : color})
                        break
                else:
                    colors.append({"Non-Hierarchical" : colors_map[None]})
            else:
                color,depth = colors_map[node]
                colors.append({depth : color})
        return colors

class EdgeColorHandler(AbstractEdgeColorHandler):
    def __init__(self,builder):
        super().__init__(builder)
            
    def hierarchy(self):
        colors = []
        color_map = _init_hierarchy_map(self)
        for edge in self._builder.v_edges():
            if edge.n not in color_map.keys():
                for o in self._builder.in_edges(edge.n):
                    o = o.n
                    if o in color_map.keys():
                        color,depth = color_map[o]
                        colors.append({f'Depth-{depth}' : color})
                        break
                else:
                    colors.append({"Non-Hierarchical" : color_map[None]})
            else:
                color,depth = color_map[edge.n]
                colors.append({f"Depth-{depth}" : color})
        return colors

def _init_hierarchy_map(handler):
    # Currently root is only one node but 
    # future proofing just in case.
    root_index = 0
    colors_map = {None : handler._color_picker[0]}
    true_root = None
    def _handle_branch(root_node,cur_col,cur_depth):
        child_color = handler._color_picker.increase_shade(cur_col)
        cur_depth +=1
        for child in handler._builder.get_children(root_node):
            child = child.v
            depth_str = f'{_get_name(true_root)}-Depth-{cur_depth}'
            colors_map[child] = (child_color,depth_str)
            _handle_branch(child,child_color,cur_depth)

    for rn in handler._builder.get_root_entities():
        root_index +=1
        true_root = rn.get_labels()[0]
        depth_str = f'{_get_name(true_root)}-Depth-0'
        colors_map[rn] = handler._color_picker[root_index],depth_str
        root_color = handler._color_picker[root_index]
        _handle_branch(rn,root_color,0)
    return colors_map

def _get_name(subject):
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