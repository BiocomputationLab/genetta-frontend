from property.property import Property
from equivalent import property_equivalent as pe
from property.property import Confidence

class SynonymProperty(Property):
    def __init__(self,range,properties=[],equivalents=[]):
        p = [Confidence()] + properties
        e = [pe.SynonymEquivalent()] + equivalents
        super().__init__(range,properties=p,equivalents=e)


