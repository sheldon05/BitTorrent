import base64
from hashlib import sha1, sha256

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

a = 'XrY7u+Ae7tCTyyK7j1rNww=='
b = b'^\xb6;\xbb\xe0\x1e\xee\xd0\x93\xcb"\xbb\x8fZ\xcd\xc3'


a1, a2, a3 = ('abc', ('123', 8080))
print(a1, a2, a3)

c = base64.b64decode(a)

string = 1

string1 = sha1(string).digest()

string1 = sha1(string).hexdigest()