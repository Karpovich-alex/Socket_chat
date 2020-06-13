import socket
import threading
import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.completion import PathCompleter, NestedCompleter
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from tools.Completer import NestedCompleter
from tools.commands import CommandARCH, Command
from Load_bar import ProgressBarOrganiser, ProgressBar, DataTransportSpeed
from contextlib import closing
import re
import traceback
import os
import sys
import time
import pickle
import cv2
import numpy

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
        self._progress = ProgressBarOrganiser(length=20)

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

    # todo: Choose file from server
    def _make_commands(self):
        with CommandARCH('Client') as self._commands:
            self._commands.add_commands(Command('help', '/h', self._com_help, description="Print all commands"))
            self._commands.add_commands(
                Command('exit user', '/e', description="Exit from server", scope='Server'))
            self._commands.add_commands(
                Command('info', '/i', description="View info", scope='Server'))
            self._commands.add_commands(
                Command('name', '/n', description="Change your name", scope='Server'))
            self._commands.add_commands(Command('send file', '/f', self._send_file, description="Send file",
                                                sub_command=(Command('image', '/img'),
                                                             Command('film', '/film'),
                                                             Command('document', '/doc'),
                                                             Command('other', '/other')),
                                                completer=PathCompleter()))
            self._commands.add_commands(
                Command('download file', '/d', self._recv_file, description="Download last file"))
        d_comp = self._commands.get_completer()

        self._prompt_completer, m_dist = NestedCompleter.from_nested_dict(d_comp)  # pattern=re.compile(r"(\/\w+)")
        self._prompt_completer(m_dist)

    async def _com_help(self, *args):
        print(self._commands.info)

    async def _recv_file(self, *args, c_bits=4096):
        reader, writer = await asyncio.open_connection(host=self._server_ip_file, port=self._server_port_file)
        writer.write(f'/d {self.__ip} {self.__port}'.encode())
        await writer.drain()
        data = await reader.read(c_bits)
        data = data.decode()
        f_type, f_size, file_name = data.split()
        f_size = int(f_size)
        while True:
            try:
                with open(buffer + file_name, 'wb') as f:
                    download = 0
                    # todo: bottom bar handler
                    loadbar = self._progress.new_bar(
                        ProgressBar(file_name, f_size, iter_speed=DataTransportSpeed('bit')),
                        action='Download')
                    data = await reader.read(c_bits)
                    while data and download < f_size:
                        f.write(data)
                        download += c_bits
                        loadbar(download)
                        if download < f_size:
                            data = await reader.read(c_bits)
            except socket.timeout:
                print("send data timeout")
            except socket.error as ex:
                print("send data error:", ex)
            except BaseException:
                # Get the traceback object
                tb = sys.exc_info()[2]
                tbinfo = traceback.format_tb(tb)[0]
                # Concatenate information together concerning the error into a message string
                pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
                print(pymsg)
            finally:
                break
        writer.close()

    async def _send_file(self, *args, c_bits=4096):
        if not args or len(args[0].split()) != 2:
            print('Please input path to file in format: /f /[type] file path')
        else:
            reader, writer = await asyncio.open_connection(host=self._server_ip_file, port=self._server_port_file)
            [msg] = args
            com = msg.split(' ', maxsplit=1)
            f_type = com[0]
            f_path: str = com[1]
            # todo: f_name
            f_name = (str(re.match(r"(.+\\)?(\w+.\w+)", f_path).group(2)))
            try:
                f_size = os.path.getsize(f_path)
                try:
                    writer.write(f"/f {f_size} {f_type} {f_name} {self.__ip} {self.__port}".encode('utf-8'))
                    await writer.drain()
                except socket.timeout:
                    print("send data timeout")
                    self.close_con()
                except socket.error as ex:
                    print("send data error:", ex)
                await asyncio.sleep(1)
                with open(f_path, 'rb') as f:
                    loadbar = self._progress.new_bar(ProgressBar(f_name, f_size, iter_speed=DataTransportSpeed('bit')),
                                                     action='Uploading')
                    loaded = 0
                    line = f.read(c_bits)
                    while line:
                        loaded += c_bits
                        loadbar(loaded)
                        try:
                            writer.write(line)
                            await writer.drain()
                        except socket.timeout:
                            print("send data timeout")
                            self.close_con()
                        except socket.error as ex:
                            print("send data error:", ex)
                        except Exception:
                            raise
                        line = f.read(c_bits)
                writer.close()
            except FileNotFoundError:
                print('Cam\'t find file %s' % f_path)

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
                        # self._thread_recv_file = Archive.Thread(target=self._load_file, args=(data,),
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
                try:
                    # asyncio.create_task(command(*com[1:]))
                    asyncio.ensure_future(command(*com[1:]))
                    # asyncio.run_coroutine_threadsafe(command(*[com[1:]]), self._loop)
                    # await command(*com[1:])
                except Exception:
                    # Get the traceback object
                    tb = sys.exc_info()[2]
                    tbinfo = traceback.format_tb(tb)[0]
                    # Concatenate information together concerning the error into a message string
                    pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
                    print(pymsg)
                # await asyncio.wait([command(*com[1:])])
                # self._loop.run_in_executor(None, command, *com[1:])
            else:
                await self._send_msg(msg.encode('utf-8'))
        else:
            print(f"Can't find this command: {com[0]}")

    async def sender(self):
        session = PromptSession(message='> ', completer=self._prompt_completer, complete_in_thread=True,
                                auto_suggest=AutoSuggestFromHistory(), refresh_interval=0.5,
                                complete_while_typing=True,
                                bottom_toolbar=self.get_bottom)  # refresh_interval=0.5,bottom_toolbar=self.get_bottom
        with patch_stdout():
            message = await session.prompt_async()
        while message != '/e':
            if message:
                if message[0] == '/':
                    try:
                        # asyncio.ensure_future(self._command_handler(message))
                        await self._command_handler(message)
                    except Exception:
                        # Get the traceback object
                        tb = sys.exc_info()[2]
                        tbinfo = traceback.format_tb(tb)[0]
                        # Concatenate information together concerning the error into a message string
                        pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(
                            sys.exc_info()[1])
                        print(pymsg)
                else:
                    await self._send_msg(message.encode('utf-8'))
            with patch_stdout():
                message = await session.prompt_async()
        await self._send_msg(message.encode('utf-8'))
        self.close_con()

    def get_bottom(self):
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
        print('DEBUG INPUT')
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
        self._loop.stop()
        exit()


if __name__ == '__main__':
    client = Client(server_adress)
    client.start()
