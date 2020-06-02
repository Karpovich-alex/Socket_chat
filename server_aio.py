import socket
import asyncio
import os


# todo: asyncio
# todo: connection with client
# todo: create users database
# todo: message types
# todo: commands
# todo: raspberry?)

# conn.settimeout(1)#timeout for connection


class Chat_server():
    def __init__(self, ip, port):
        self._ip_server = ip
        self._port_server = port

    @staticmethod
    def print_th(text):
        print(text)

    async def _handle_connection(self, reader:asyncio.StreamReader, writer:asyncio.StreamWriter):
        # data = await reader.read(1024)
        # message = data.decode()
        # addr = writer.get_extra_info('peername')
        # print("Received %r from %r" % (message, addr))
        # writer.close()
        while True:
            addr = writer.get_extra_info("peername")
            # data = await reader.read(1024)
            try:
                data = await reader.read(1024)
            except ConnectionResetError:
                self.print_th(f'User {addr} exit')
                writer.close()
                break
            except asyncio.TimeoutError as error:
                print(f'{addr}: WEBSOCKET_TIMEOUT: {error}')
                writer.close()
                break
            if data:
                message = data.decode()
                print("received %r from %r" % (message, addr))


    def start(self):
        loop = asyncio.get_event_loop()
        coro = asyncio.start_server(self._handle_connection, self._ip_server, self._port_server, loop=loop)
        server = loop.run_until_complete(coro)
        print('Serving on {}'.format(server.sockets[0].getsockname()))
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass

        # Close the server
        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.close()

def process_request(conn, addr):
    print('Connected client: {} to {} pid'.format(addr, os.getpid()))

    with conn:
        conn.sendto("Добро пожаловать на супер чат! введите имя через 'name:'\n".encode('utf8'), addr)
        info = 'Ваш id: {}'.format(addr)
        conn.sendto(info.encode('utf8'), addr)
        while True:
            try:
                data = conn.recv(1024)
            except socket.timeout:
                print_th('close connection')
                break

            if not data or data.decode('utf8').strip() == '/e':
                print_th('{} go out'.format(addr))
                break
            print_th(check_name(data.decode('utf8'), addr))
            conn.sendto(data, ('0.0.0.0', 0))
            # check_name(data.decode('utf8'), addr)


def check_name(text, addr):
    if text[:5] == 'name:':
        database('add', addr, text[5:].strip())
        return f'Your name: {text[5:].strip()}'
    else:
        if database('check', addr):
            return ('{id} > {mes}'.format(mes=text, id=memory[addr]))
        else:
            return ('{id} > {mes}'.format(mes=text, id=addr))


def database(op, addr, name=None):
    with m_lock:
        if op == 'check':
            return addr in memory
        elif op == 'add':
            memory[addr] = name
            return None


def worker(sock):
    while True:
        conn, addr = sock.accept()
        # print("pid", os.getpid())
        th = threading.Thread(target=process_request, args=(conn, addr))
        th.start()


def main():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 10001))
        sock.listen(socket.SOMAXCONN)
        # print_th('Main pid: {}'.format(os.getpid()))

        workers_count = 3
        workers_list = [multiprocessing.Process(target=worker, args=(sock,))
                        for _ in range(workers_count)]

        for w in workers_list:
            w.start()

        for w in workers_list:
            w.join()


if __name__ == '__main__':
    # main()
    server = Chat_server("127.0.0.1", 10001)
    server.start()
