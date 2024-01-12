from app.tools.graph_query.datatype_handlers.canonical import CanonicalHandler
from app.tools.graph_query.datatype_handlers.derivative import DerivativeHandler
from app.tools.graph_query.datatype_handlers.interaction import InteractionHandler
from app.tools.graph_query.datatype_handlers.metadata import MetadataHandler
from app.tools.graph_query.datatype_handlers.sequence import SequenceHandler
from app.tools.graph_query.datatype_handlers.modules import ModuleHandler
class GraphQueryHandler:
    def __init__(self,graph):
        self._graph = graph
        self._handlers = [CanonicalHandler(graph),
                        DerivativeHandler(graph),
                        InteractionHandler(graph),
                        MetadataHandler(graph),
                        SequenceHandler(graph),
                        ModuleHandler(graph)]

    def get_handlers(self):
        return self._handlers

    def query(self,datatype,query,strict=False):
        for handler in self._handlers:
            if handler.get_name() == datatype:
                return handler.handle(query,strict=strict)
        raise ValueError(f'{datatype} is not a valid datatype.')
    
    def feedback(self,datatype,source,result,positive=True):
        for handler in self._handlers:
            if handler.get_name() == datatype:
                return handler.feedback(source,result,positive=positive)
        raise ValueError(f'{datatype} is not a valid datatype.')