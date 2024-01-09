class Procedures():
    def __init__(self, graph):
        self._graph = graph
        self._driver = self._graph.driver

    def dfs(self, name, source, dest=None, mode="stream"):
        return self._driver.procedures.path_finding.dfs(name, source, dest, mode=mode)

    def bfs(self, name, source, dest=None, mode="stream"):
        return self._driver.procedures.path_finding.bfs(name, source, dest, mode=mode)

    def louvain(self,name):
        return self._driver.procedures.community_detection.louvain(name)

    def label_propagation(self,name):
        return self._driver.procedures.community_detection.label_propagation(name)

    def is_connected(self, name):
        return len(set([c["componentId"] for c in 
        self._driver.procedures.community_detection.wcc(name)])) == 1

    def get_components(self,name):
        components = {}
        for e in self._driver.procedures.community_detection.wcc(name):
            c_id = e["componentId"]
            if c_id not in components:
                components[c_id] = []
            components[c_id].append(e["node"])
        return list(components.values())

    def node_similarity(self,name):
        return self._driver.procedures.similarity.node(name)


    def degree(self,name,orientation="NATURAL"):
        return {n["node"]:n["score"] for n in 
                self._driver.procedures.centrality.degree(
                    name,orientation=orientation)}
    
    def get_inputs(self,name):
        return [s["node"] for s in 
                self._driver.procedures.centrality.degree(name,
                                        orientation="REVERSE") 
                                        if s["score"] == 0.0]
    
    def get_outputs(self,name):
        return [s["node"] for s in 
                self._driver.procedures.centrality.degree(name)
                if s["score"] == 0.0]

    def dijkstra_sp(self,name,source,target):
        return self._driver.procedures.path_finding.dijkstra_sp(name,
                                                                source,
                                                                target)