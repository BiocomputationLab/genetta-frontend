from entities.abstract_entity import ConceptualEntity,PhysicalEntity
from equivalent import synonym_equivalent as se
from property import reactions


class Synonym(ConceptualEntity):
    def __init__(self,equivalents=[]):
        if equivalents == []:
            r = [se.SynonymRoleEquivalent()]
        else:
            r = equivalents
        super().__init__(equivalents=r)
