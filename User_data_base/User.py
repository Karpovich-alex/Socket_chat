class User:
    def __init__(self, addr, reader, writer):
        self.addr = addr
        self._ip = addr[0]
        self._port = addr[1]
        self.reader = reader
        self.writer = writer
        self.name = hash(f'{self._ip} {self._port}')

    def __hash__(self):
        return hash(f'{self._ip} {self._port}')
