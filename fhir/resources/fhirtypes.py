class CodeableConceptType(dict):
    def __init__(self, text=""):
        super().__init__(text=text)

class IdentifierType(dict):
    def __init__(self, value=""):
        super().__init__(value=value)

class ReferenceType(dict):
    def __init__(self, reference=""):
        super().__init__(reference=reference)
