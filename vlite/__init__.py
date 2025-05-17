class VLite:
    def __init__(self, *args, **kwargs):
        self.items = []
    def count(self):
        return len(self.items)
    def add(self, item_id=None, data=None, metadata=None):
        self.items.append((item_id, data, metadata))
    def save(self):
        pass
    def get(self, where=None):
        return 1
    def delete(self, id):
        pass
    def retrieve(self, text=None, top_k=1, return_scores=True):
        return []
