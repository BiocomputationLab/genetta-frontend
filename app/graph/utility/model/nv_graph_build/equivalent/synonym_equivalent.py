from equivalent.abstract_equivalent import ConceptualEquivalent
from restriction import synonym_restriction as sr

class SynonymRoleEquivalent(ConceptualEquivalent):
    def __init__(self):
        restrictions = [sr.SynonymRoleRestriction()]
        super().__init__(restrictions)