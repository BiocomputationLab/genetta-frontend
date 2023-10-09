from restriction.abstract_restriction import RoleRestriction
from identifiers import identifiers

class SynonymRoleRestriction(RoleRestriction):
    def __init__(self):
        values = [identifiers.roles.synonym]
        super().__init__(values)