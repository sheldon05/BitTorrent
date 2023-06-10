class Prueba:
    def __init__(self, a, b):
        self.a = a
        self.b = b
    def __getstate__(self):
        return {
            'a':self.a,
            'b':self.b
        }
    def __setstate__(self,state):
        self.a = state['a']
        self.b = state['b']
    def __str__(self):
        return 'soy la clase prueba'