import socket
import threading
import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from contextlib import closing

# todo: принимать сообщения сервер
p_lock = threading.RLock()
server_adress = ("127.0.0.1", 10001)

loop = asyncio.get_event_loop()


class Client:
    def __init__(self, server_info):
        self._server_ip, self._server_port = server_info

    def start(self):
        try:
            print(f'Try to connect : {(self._server_ip, self._server_port)}')
            self.sock = socket.create_connection((self._server_ip, self._server_port))
            print('Your ip: {}'.format(self.sock.getsockname()))
        except socket.timeout:
            exit('Server not found')
        except socket.error as ex:
            exit(f'Got unexpected error: {ex}')
        thread_recv=threading.Thread(target=self.recvive_msg, name="reciev_message")
        self._loop = asyncio.get_event_loop()
        thread_recv.start()
        with closing(self._loop) as event_loop:
            event_loop.run_until_complete(self.sender())

    def recvive_msg(self):
        while True:
            try:
               data = self.sock.recv(1024)
            except ConnectionAbortedError:
                self.close_con()
            except ConnectionResetError:
                print('Server disconnected')
                self.close_con()
            except socket.error as ex:
                print("send data error:", ex)
                self.close_con()
            if data:
                print(data.decode('utf8'))

    async def _recieve_msg(self):
        while True:
            try:
                data = await self._reader.read(1024)
            except ConnectionResetError:
                self.print_th(f'Server {self._addr} exit')
                self._writer.close()
                return f'Server {self._addr} exit'

            except asyncio.TimeoutError as error:
                print(f'{self._addr}: WEBSOCKET_TIMEOUT: {error}')
                self._writer.close()
                return f'{self._addr}: WEBSOCKET_TIMEOUT: {error}'
            except asyncio.CancelledError:
                self.print_th('This error')
                self._writer.close()
                return 'CancelledError'

            if data:
                message = data.decode()
                self.print_th("received %r from %r" % (message, self._addr))



    async def sender(self):
        session = PromptSession()
        with patch_stdout():
            message = await session.prompt_async('> ')
        while message != '/e':
            try:
                # await asyncio.get_event_loop().run_in_executor(None, sock.send(message.encode('utf-8')))
                self.sock.send(message.encode('utf-8'))
            except socket.timeout:
                print("send data timeout")
                break
            except socket.error as ex:
                print("send data error:", ex)
                break
            with patch_stdout():
                message = await session.prompt_async('> ')
        try:
            self.sock.send(message.encode("utf8"))
        except ConnectionResetError:
            print('Server disconnected')
        except socket.error as ex:
            print("send data error:", ex)
        self.close_con()

    def close_con(self):
        self.sock.close()
        self._loop.stop()
        exit()


if __name__ == '__main__':
    client = Client(server_adress)
    client.start()
