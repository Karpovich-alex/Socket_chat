import socket
import threading
import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from contextlib import closing
from tools.commands import CommandARCH, Command

# todo: принимать сообщения сервер
p_lock = threading.RLock()
server_adress = ("127.0.0.1", 10001)
DB = True
loop = asyncio.get_event_loop()


class Client:
    def __init__(self, server_info):
        self._server_ip, self._server_port = server_info
        self._commands = CommandARCH('Client')
        self._make_commands()

    def _make_commands(self):
        self._commands.add_commands(Command('help', '/h', self._com_help, description="Print all commands"))

    async def _com_help(self, *args):
        print(self._commands.get_info())

    def start(self):
        try:
            print(f'Try to connect : {(self._server_ip, self._server_port)}')
            self.sock = socket.create_connection((self._server_ip, self._server_port))
            print('Your ip: {}'.format(self.sock.getsockname()))
        except socket.timeout:
            exit('Server not found')
        except socket.error as ex:
            exit(f'Got unexpected error: {ex}')
        thread_recv = threading.Thread(target=self.recvive_msg, name="reciev_message")
        self._loop = asyncio.get_event_loop()
        thread_recv.start()
        with closing(self._loop) as event_loop:
            if DB:
                event_loop.run_until_complete(self.sender_DB())
            else:
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

    async def _command_handler(self, msg: str):
        com = msg.split(' ', maxsplit=1)
        if self._commands.check_com(com[0]):
            await self._commands.get_com(com[0])(*com[1:])
        else:
            print(f"Can't find this command: {com}")

    async def sender(self):
        session = PromptSession()
        with patch_stdout():
            message = await session.prompt_async('> ')
        while message != '/e':
            if message[0] == '/':
                await self._command_handler(message)
            else:
                try:
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

    async def sender_DB(self):
        message = await self._loop.run_in_executor(None, input)
        while message != '/e':
            if message[0] == '/':
                await self._command_handler(message)
            else:
                try:
                    self.sock.send(message.encode('utf-8'))
                except socket.timeout:
                    print("send data timeout")
                    break
                except socket.error as ex:
                    print("send data error:", ex)
                    break
            message = await self._loop.run_in_executor(None, input)
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
