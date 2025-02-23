import random

class Content:
    def __init__(self,id):
        print(f"Create Content {id}")
        self._id = id
        self._values = []
        for i in range(id):
            self._values.append(Content(id-1))
            
    def data(self):
        yield f"Content: {self._id}"
        for c in self._values:
            yield from c.data()
            
class Headers:
    def __init__(self):
        self._values = {}
        for i in range(10):
            name = ''.join([random.choice('abcde') for i in range(10)])
            val = ''.join([random.choice('abcde') for i in range(10)])
            self._values[name] = val
            
    def data(self):
        for name,val in self._values.items():
            yield f"{name}: {val}"
            
c = Content(3)
h = Headers()

class Writer:
    def __init__(self,providers):
        for provider in providers:
            self.write(provider.data())
            
    def write(self,data):
        while True:
            try:
                print(next(data))
            except StopIteration:
                break

            