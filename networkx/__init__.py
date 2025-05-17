class Graph:
    def __init__(self):
        self._nodes = {}
        self._edges = []
    def add_node(self, n, **attrs):
        self._nodes[n] = attrs
    def add_edge(self, u, v, **attrs):
        self._edges.append((u, v, attrs))
    def nodes(self, data=False):
        if data:
            return self._nodes.items()
        return list(self._nodes.keys())
    def edges(self, data=False):
        if data:
            return self._edges
        return [(u,v) for u,v,_ in self._edges]
