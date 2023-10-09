from entities.abstract_entity import ConceptualEntity
from entities.abstract_entity import PhysicalEntity 
from property.property import PositionOf
from property.property import Next


class Position(ConceptualEntity):
    def __init__(self,properties=[],equivalents=[],restrictions=[]):
        if equivalents == []:
            equiv = []
        else:
            equiv = equivalents
        if restrictions == []:
            res = []
        else:
            res = restrictions
        p = properties + [PositionOf(PhysicalEntity),
                          Next(Position)]
        super().__init__(properties=p,
        equivalents=equiv,restrictions=res)