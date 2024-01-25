import os
from app.graph.world_graph import WorldGraph
from app.tools.kg_expansion.builder import TruthGraphBuilder


db_host = os.environ.get('NEO4J_HOST', 'localhost')
db_port = os.environ.get('NEO4J_PORT', '7687')
db_auth = os.environ.get('NEO4J_AUTH', "neo4j/Radeon12300")
db_auth = tuple(db_auth.split("/"))
uri = f'neo4j://{db_host}:{db_port}' 
login_graph_name = "login_manager"

graph = WorldGraph(uri,db_auth,reserved_names=[login_graph_name])
tg_builder = TruthGraphBuilder(graph)

if __name__ == "__main__":
    tg_builder.expand()