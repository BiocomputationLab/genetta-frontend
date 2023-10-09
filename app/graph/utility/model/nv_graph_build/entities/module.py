from entities.abstract_entity import ConceptualEntity
from entities.interaction import Interaction
from property.property import HasInteraction

class Module(ConceptualEntity):
    def __init__(self,properties=[],equivalents=[],restrictions=[]):
        if equivalents == []:
            equiv = []
        else:
            equiv = equivalents
        if restrictions == []:
            res = []
        else:
            res = restrictions
        p = properties + [HasInteraction([Interaction])]
        super().__init__(properties=p,
        equivalents=equiv,restrictions=res)
