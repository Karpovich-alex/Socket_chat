class User:
    def __init__(self, addr, reader, writer):
        self.addr = addr
        self._ip = addr[0]
        self._port = addr[1]
        self.reader = reader
        self.writer = writer
        self.name = f'{self._ip} {self._port}'
