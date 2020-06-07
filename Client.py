import socket
import threading
import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.completion import WordCompleter
# from prompt_toolkit.shortcuts import ProgressBar
from contextlib import closing
from tools.commands import CommandARCH, Command
from Load_bar import ProgressBar
import time
import pickle
import cv2
import numpy
import os

# todo: принимать сообщения сервер
p_lock = threading.RLock()
server_adress = ("127.0.0.1", 10001)
DB = False
loop = asyncio.get_event_loop()
buffer = 'client_buffer/'
recv_lock = threading.RLock()


class Client:
    def __init__(self, server_info):
        self._server_ip, self._server_port = server_info
        self._make_commands()

    def _make_commands(self):
        with CommandARCH('Client') as self._commands:
            self._commands.add_commands(Command('help', '/h', self._com_help, description="Print all commands"))
            self._commands.add_commands(
                Command('exit user', '/e', description="Exit from server", scope='Server'))
            self._commands.add_commands(
                Command('info', '/i', description="View info", scope='Server'))
            self._commands.add_commands(
                Command('name', '/n', description="Change your name", scope='Server'))
            self._commands.add_commands(Command('send file', '/f', self._send_file, description="Send file"))
            self._commands.add_commands(Command('load file', '/d', self._req_load, description="Download last file"))
        arr, d_comp = self._commands.get_completer()
        # todo: AUTO tab
        self._prompt_completer = WordCompleter(arr, meta_dict=d_comp)

    async def _com_help(self, *args):
        print(self._commands.info)

    async def _req_load(self, *args):
        await self._send_msg('/d'.encode('utf8'))

    def _load_file(self, *args):
        with recv_lock:
            f_type, f_size, file_name = args[0].split()
            f_size = int(f_size)
            print(f'Download {file_name} type: {f_type} size: {f_size} b')
            try:
                with open(buffer + file_name, 'wb') as f:
                    # todo: add TRY
                    downloaded_size = 0
                    loadbar = ProgressBar(f"upload {file_name}", f_size)
                    data = self.sock.recv(1024)
                    while downloaded_size < f_size and data:
                        f.write(data)
                        downloaded_size += len(data)
                        loadbar(downloaded_size)
                        if downloaded_size < f_size:
                            data = self.sock.recv(1024)
                loadbar.end(text=f"File {file_name} has downloaded")
            except BaseException as ex:
                print(f"Got unexcepted error: {ex}")

    async def _send_file(self, *args):
        if not args:
            print('Please input path to file')
        else:
            [msg] = args
            com = msg.split(' ', maxsplit=1)
            f_type = com[0]
            f_path: str = com[1]
            try:
                f_size = os.path.getsize(f_path)
                await self._send_msg(f"/f {f_type} {f_size} {f_path}".encode('utf-8'))
                await asyncio.sleep(1)
                loadbar = ProgressBar(f"upload {f_path}", f_size)
                loaded = 0
                loadbar(loaded)
                with open(f_path, 'rb') as f:
                    line = f.read(1024)
                    while line:
                        loaded += 1024
                        loadbar(loaded)
                        self.sock.sendall(line)
                        line = f.read(1024)
                loadbar.end()
            except FileNotFoundError:
                print('Cam\'t find file %s' % f_path)

    def start(self):
        try:
            print(f'Try to connect : {(self._server_ip, self._server_port)}')
            self.sock = socket.create_connection((self._server_ip, self._server_port))
            print('Your ip: {}'.format(self.sock.getsockname()))
        except socket.timeout:
            exit('Server not found')
        except socket.error as ex:
            exit(f'Got unexpected error: {ex}')
        self._thread_recv = threading.Thread(target=self.receive_msg, name="recieve_message")
        self._loop = asyncio.get_event_loop()
        self._thread_recv.start()
        with closing(self._loop) as event_loop:
            if DB:
                event_loop.run_until_complete(self.sender_DB())
            else:
                event_loop.run_until_complete(self.sender())

    def receive_msg(self):
        while True:
            try:
                with recv_lock:
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
                try:
                    data = data.decode('utf8')
                    if data.startswith('/') and data.find('>>') == -1:
                        self._thread_recv_file = threading.Thread(target=self._load_file, args=(data,),
                                                                  name='Receiving file')
                        self._thread_recv_file.start()
                        # time.sleep(2)
                        with recv_lock:
                            self._thread_recv_file.join()
                    print(data)
                except UnicodeDecodeError:
                    pass

    async def _command_handler(self, msg: str):
        com = msg.split(' ', maxsplit=1)
        if self._commands.check_com(com[0]):
            command = self._commands.get_com(com[0])
            if command.get_scope() == 'Client':
                await command(*com[1:])
            else:
                await self._send_msg(msg.encode('utf-8'))
        else:
            print(f"Can't find this command: {com[0]}")

    async def sender(self):
        session = PromptSession()
        with patch_stdout():
            message = await session.prompt_async('> ', completer=self._prompt_completer)
        while message != '/e':
            if message[0] == '/':
                await self._command_handler(message)
            else:
                await self._send_msg(message.encode('utf-8'))
            with patch_stdout():
                message = await session.prompt_async('> ', completer=self._prompt_completer)
        await self._send_msg(message.encode('utf-8'))
        self.close_con()

    async def _send_msg(self, message: bytes):
        try:
            self.sock.send(message)
        except socket.timeout:
            print("send data timeout")
            self.close_con()
        except socket.error as ex:
            print("send data error:", ex)

    async def sender_DB(self):
        message = await self._loop.run_in_executor(None, input)
        while message != '/e':
            if message[0] == '/':
                await self._command_handler(message)
            else:
                await self._send_msg(message.encode('utf-8'))
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
