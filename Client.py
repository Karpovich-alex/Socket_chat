import socket
import threading
import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.lexers import RegexSync
# from prompt_toolkit.shortcuts import ProgressBar
from contextlib import closing
from tools.commands import CommandARCH, Command
from Load_bar import ProgressBar, ProgressBarOrganaser
import re
import tracemalloc
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
send_lock = threading.RLock()


class Client:
    def __init__(self, server_info):
        self._server_ip, self._server_port = server_info
        self._make_commands()
        # Info about file server acceptor
        self._server_port_file = 0
        self._server_ip_file = self._server_ip
        self._file_sock = 0
        self._progress = ProgressBarOrganaser()

    def start(self):
        try:
            print(f'Try to connect : {(self._server_ip, self._server_port)}')
            self.sock = socket.create_connection((self._server_ip, self._server_port))
            print('Your ip: {}'.format(self.sock.getsockname()))
            self.__ip, self.__port = self.sock.getsockname()
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
            self._commands.add_commands(
                Command('download file', '/d', self._recv_file, description="Download last file"))
            self._commands.add_commands(Command('test', '/t', self._test))
        arr, d_comp = self._commands.get_completer()
        # todo: AUTO tab
        self._prompt_completer = WordCompleter(arr, meta_dict=d_comp)  # pattern=re.compile(r"(\/\w+)")

    def _com_help(self, *args):
        print(self._commands.info)

    async def _test(self, *args):
        print('Start sleep')
        time.sleep(4)
        print('sleeped')

    async def _req_load(self, *args):
        await self._send_msg('/d'.encode('utf8'))

    async def _recv_file(self, *args, c_bits=4096):
        self._file_sock = socket.create_connection((self._server_ip, self._server_port_file))
        self._file_sock.sendall(f'/d {self.__ip} {self.__port}'.encode())
        data = self._file_sock.recv(c_bits).decode()
        f_type, f_size, file_name = data.split()
        f_size = int(f_size)
        print(f'Download {file_name} type: {f_type} size: {f_size} b')
        try:
            with open(buffer + file_name, 'wb') as f:
                try:
                    downloaded_size = 0
                    loadbar = self._progress.new_bar(file_name, f_size, 'Downloading', p=False)
                    data = self._file_sock.recv(c_bits)
                    while downloaded_size < f_size and data:
                        f.write(data)
                        downloaded_size += len(data)
                        loadbar(downloaded_size)
                        if downloaded_size < f_size:
                            data = self._file_sock.recv(c_bits)
                except socket.timeout:
                    print("send data timeout")
                    self.close_con()
                except socket.error as ex:
                    print("send data error:", ex)

        except BaseException as ex:
            print(f"Got unexcepted error: {ex}")

    async def _send_file(self, *args, c_bits=4096):
        if not args:
            print('Please input path to file')
        else:
            self._file_sock = socket.create_connection((self._server_ip, self._server_port_file))
            # self._file_sock = self._loop.open_connection(host=self._server_ip_file, port=self._server_port_file)
            [msg] = args
            com = msg.split(' ', maxsplit=1)
            f_type = com[0]
            f_path: str = com[1]
            # todo: f_name
            # f_name  =f_path.rfind('/')
            try:
                f_size = os.path.getsize(f_path)
                try:
                    self._file_sock.send(f"/f {f_size} {f_type} {f_path} {self.__ip} {self.__port}".encode('utf-8'))
                except socket.timeout:
                    print("send data timeout")
                    self.close_con()
                except socket.error as ex:
                    print("send data error:", ex)
                await asyncio.sleep(1)
                # send_th = threading.Thread(target=self._send_file_thread, args=(f, c_bits, f_size, f_path), name='Send thread')
                # await self._send_file_thread(f, c_bits, f_size, f_path)
                self._loop.run_in_executor(None, self._send_file_thread, c_bits, f_size, f_path)
                # send_th.start()
                # with send_lock:
                #     send_th.join()
                # loadbar.end()

            except FileNotFoundError:
                print('Cam\'t find file %s' % f_path)
        self._file_sock.close()

    def _send_file_thread(self, c_bits, f_size, f_path):
        with open(f_path, 'rb') as f:
            with send_lock:
                print('Here')
                loadbar = self._progress.new_bar(f_path, f_size, 'Uploading', p=False)
                loaded = 0
                line = f.read(c_bits)
                while line:
                    loaded += c_bits
                    loadbar(loaded)
                    try:
                        self._file_sock.sendall(line)
                    except socket.timeout:
                        print("send data timeout")
                        self.close_con()
                    except socket.error as ex:
                        print("send data error:", ex)
                    line = f.read(c_bits)
                print('There')

    def receive_msg(self):
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
                try:
                    data = data.decode('utf8')
                    if data.startswith('///'):  # init message
                        self._server_port_file = int(re.match(r"\d*", data.split()[1])[0])
                    elif 0:
                        pass
                        # if data.startswith('/') and data.find('>>') == -1:
                        # self._thread_recv_file = threading.Thread(target=self._load_file, args=(data,),
                        #                                       name='Receiving file')
                        # self._thread_recv_file.start()
                        # time.sleep(2)
                        # with recv_lock:
                        #     self._thread_recv_file.join()
                    else:
                        print(data)
                except UnicodeDecodeError:
                    pass

    async def _command_handler(self, msg: str):
        com = msg.split(' ', maxsplit=1)
        if com[0] in self._commands:
            command = self._commands.get_com(com[0])
            if command.get_scope() == 'Client':
                asyncio.create_task(command(*com[1:]))
                # await asyncio.wait([command(*com[1:])])
                # self._loop.run_in_executor(None, command, *com[1:])
            else:
                await self._send_msg(msg.encode('utf-8'))
        else:
            print(f"Can't find this command: {com[0]}")

    async def sender(self):
        session = PromptSession(message='> ', completer=self._prompt_completer, complete_in_thread=True,
                                bottom_toolbar=self.get_rprompt, refresh_interval=1)
        with patch_stdout():
            message = await session.prompt_async()
        while message != '/e':
            if message:
                if message[0] == '/':
                    await self._command_handler(message)
                else:
                    await self._send_msg(message.encode('utf-8'))
            with patch_stdout():
                message = await session.prompt_async()
        await self._send_msg(message.encode('utf-8'))
        self.close_con()

    def get_rprompt(self):
        return self._progress.get_progress()

    async def _send_msg(self, message: bytes):
        try:
            self.sock.send(message)
        except socket.timeout:
            print("send data timeout")
            self.close_con()
        except socket.error as ex:
            print("send data error:", ex)

    async def sender_DB(self):
        message = await self._loop.run_in_executor(None, input, '> ')
        while message != '/e':
            if message and message[0] == '/':
                await self._command_handler(message)
            else:
                await self._send_msg(message.encode('utf-8'))
            message = await self._loop.run_in_executor(None, input, '> ')
        try:
            self.sock.send(message.encode("utf8"))
        except ConnectionResetError:
            print('Server disconnected')
        except socket.error as ex:
            print("send data error:", ex)
        self.close_con()

    def close_con(self):
        self.sock.close()
        try:
            self._file_sock.close()
        except:
            pass
        self._loop.stop()
        exit()


if __name__ == '__main__':
    client = Client(server_adress)
    client.start()
