import Pyro4

class MyObject:
    def hello(self):
        return "Hello from node1!"

# Iniciamos una instancia de Pyro4 y registramos nuestro objeto
daemon = Pyro4.Daemon(port=9091)
ns = Pyro4.locateNS()
uri = daemon.register(MyObject)
ns.register("myobject.node1", uri)

# Iniciamos el bucle del servidor Pyro4
print("Ready!")
daemon.requestLoop()