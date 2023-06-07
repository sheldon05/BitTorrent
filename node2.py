import Pyro4

# Buscamos la URI del objeto MyObject registrado en el otro nodo
uri = Pyro4.Proxy("PYRO:myobject.node1@172.20.0.2:9091")

# Llamamos al método hello() del objeto remoto
print(uri.hello())