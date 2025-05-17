class BaseLoader:
    pass

class Template:
    def __init__(self, text=""):
        self.text = text
    def render(self, *args, **kwargs):
        return self.text

class Environment:
    def __init__(self, *args, **kwargs):
        pass
    def get_template(self, name):
        return Template()

def select_autoescape(*args, **kwargs):
    return None
