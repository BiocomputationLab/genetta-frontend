from app.tools.enhancer.enhancements.abstract_enhancements import AbstractEnhancement
from app.tools.enhancer.enhancements.interaction.protein_production import DesignProteinProduction
from app.tools.enhancer.enhancements.canonical.canonicaliser import DesignCanonicaliser

class DesignEnhancements(AbstractEnhancement):
    def __init__(self,world_graph,miner):
        super().__init__(world_graph,miner,[DesignCanonicaliser,
                                            DesignProteinProduction])