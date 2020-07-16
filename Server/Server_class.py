import asyncio
from typing import Tuple
from Server.User_data_base.UserDB import UserDB
from Server.config import IP, PORT, buffer, PORT_FILES
import logging
import traceback
from tools.commands import CommandARCH, Command
from Server.Server_chat import AbstractServer
from Server.Model import DataBaseConnection
from tools.message.message import Message, DataContainer
# todo: command_handler
# todo: user login timeout
# todo: command server class
# todo: critical error feedback
logger = logging.getLogger("tools.logger_example.server")


class ChatServer(AbstractServer):
    def __init__(self, ip, port, port_files):
        self._ip_server = ip
        self._port_server = port
        self._port_server_file = port_files
        self._user_db: UserDB = UserDB()
        self._data_base = DataBaseConnection()

        # todo: new description
        self._description = '''
        Hi there. This is the Socket Chat
        now there {} users
        Enter /h to see all commands
        '''
        self._welcome_msg = f'///welcome {self._port_server_file}'
        self._last_file = '/img 25405 cat.jpg'
        self._set_commands()

    def _set_commands(self):
        """
        Helps Server handle messages and assign data_type with function
        """
        with CommandARCH('Users') as self._user_commands:
            self._user_commands.add_command(
                Command('exit user', '/e', self._u_exit, description="Exit from server", scope='Server'))
            self._user_commands.add_command(
                Command('info', '/i', self._u_info, description="View info", scope='Server'))
            self._user_commands.add_command(
                Command('name', '/n', self._u_set_name, description="Change your name", scope='Server'))
            # self._user_commands.add_commands(Command('Accept file', '/f', self._recieve_file))
            # self._user_commands.add_commands(Command('Send file', '/d', self._u_send_file))
            # self._user_commands.add_commands(Command('add files port', '/fp', self._u_add_port))

    # todo: fix
    async def _u_send_file(self, addr, *args):
        if self._last_file:
            await self._r_send_msg(self._last_file.encode(), addr)
            f_type, f_size, file_name = self._last_file.split()
            logger.info(f"User {addr} start recv {file_name}")
            await asyncio.sleep(2)
            with open(buffer + file_name, 'rb') as f:
                # todo: add TRY
                line = f.read(1024)
                while line:
                    await self._r_send_msg(line, addr)
                    line = f.read(1024)
            await self.send_msg(f"file {file_name} has downloaded", to_user=addr)
            logger.info(f"User {addr} received aaa {file_name}")

        else:
            await self.send_msg(f"Can't find last file", to_user=addr)

    async def _u_set_name(self, addr, *name):
        if name:
            [name] = name
            await self._user_db.set_name(addr, name)
            await self.send_msg(f'Your name is {name}', to_user=addr, m_type='notice')
        else:
            await self.send_msg(f"You can't be named ' '", to_user=addr, m_type='notice')

    async def _u_info(self, addr, *args):
        msg = self._user_db.info_users()
        await self.send_msg(msg, to_user=addr)

    async def _u_exit(self, addr, *args):
        user = self._user_db.get_user(addr)
        writer: asyncio.StreamWriter = user.writer
        # reader: asyncio.StreamReader = user.reader
        # todo: fix exit
        writer.close()
        await self._loop.run_in_executor(None, self._user_db.del_user, addr)
        await self.send_msg(f"User {user.name} exit")
        logger.info(f"User {user.addr} exit")

    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        Create new connection. Take from server params for user, save them and handle new messages from user.
        :param reader: Reader object
        :param writer: Writer object
        :return:
        """
        await self._data_base.prepare()
        addr = writer.get_extra_info("peername")
        await self._handle_new_connection(addr, reader, writer)
        while True:
            try:
                data = await reader.read(1024)
            except ConnectionResetError as error:
                # logger.error(f'{addr}: WEBSOCKET_CONNECTION_ERROR: {error}')
                break
            except asyncio.TimeoutError as error:
                logger.error(f'{addr}: WEBSOCKET_TIMEOUT: {error}')
                break
            except BaseException as ex:
                logger.critical("Uncaught exception: %s", ex)
                break
            if addr not in self._user_db.get_all_users():
                break
            if data:
                message = data.decode()
                logger.info("{} >> {}".format(addr, message))
                await self._data_base.add_message(from_user=self._data_base.get_user_id(addr), to_user=0, message_text=message,
                                                  message_type='text')
                if message[0] == '/':
                    await self._user_commands_handler(message, addr)
                else:
                    await self.send_msg(message, from_user=addr)
        if addr in self._user_db.get_all_users():
            await self._u_exit(addr)

    async def _handle_new_connection(self, addr, reader, writer):
        """
        Handle new connection. Send settings to client
        :param addr: Tuple(ip, port)
        :param reader:
        :param writer:
        :return:
        """
        logger.info(f"User {addr} has connected")
        data = await reader.read(1024)
        await self._data_base.add_user(login=str(addr[0] + ' '+str(addr[1])), password='')
        await self.send_msg("{} : User {} has connected".format('{}', addr), m_type='notice')
        await asyncio.sleep(0.1)
        await self._user_db.add_user(addr, reader, writer)
        await self._r_send_msg(self._welcome_msg.encode(), to_user=addr)
        await asyncio.sleep(0.1)
        await self.send_msg(
            self._description.format(self._user_db.get_num_users()),
            to_user=addr, m_type='notice')

    # todo: message verification
    async def _message_handler(self, data):
        message = DataContainer.from_binary(data)

    async def _user_commands_handler(self, command: str, addr: Tuple):
        """
        Handle user commands which begins with /
        :param command: Command
        :param addr: Tuple(ip, port)
        :return:
        """
        commands = command.split(' ', maxsplit=1)
        command = commands[0]
        if command in self._user_commands:
            com = self._user_commands.get_com(command)
            # todo: Check await
            await com(addr, *commands[1:])
        else:
            await self.send_msg('Unsupported command', to_user=addr)

    async def _send_file(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, data, c_bits=4096):
        addr = writer.get_extra_info("peername")
        client_ip, client_port = data
        client_port = int(client_port)
        # todo: add data handler
        if self._last_file:
            writer.write(self._last_file.encode())
            await writer.drain()
            # await asyncio.sleep(1)
            f_type, f_size, file_name = self._last_file.split()
            logger.info(f"User ({client_ip}, {client_port}) start recv {file_name}")
            # await asyncio.sleep(1)
            try:
                while True:
                    with open(buffer + file_name, 'rb') as f:
                        try:
                            line = f.read(c_bits)
                            while line:
                                writer.write(line)
                                await writer.drain()
                                line = f.read(c_bits)
                        except ConnectionResetError as ex:
                            logger.info(f"User_files {addr} has lost connection")
                            break
                        except BaseException as ex:
                            logger.critical("Uncaught exception: %s", ex)
                            break
                        await self.send_msg("{} : File {} has downloaded".format('{}', file_name),
                                            m_type='notice', to_user=(client_ip, client_port))
                        logger.info(f"User ({client_ip}, {client_port}) received {file_name}")
                        break
            except FileNotFoundError:
                await self.send_msg("{} : Can't find file {}".format('{}', file_name), m_type='notice',
                                    to_user=(client_ip, client_port))
                logger.info("Can't find file {}".format(file_name))
                writer.write(''.encode())
            except BaseException as ex:
                logger.critical("Uncaught exception: %s", ex)
        else:
            await self.send_msg(f"Can't find last file", to_user=addr)

    async def _receive_file(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, data, c_bits=4096):
        addr = writer.get_extra_info("peername")
        if len(data) == 5:
            f_size, f_type, file_name, client_ip, client_port = data
            f_size = int(f_size)
            client_port = int(client_port)
            self._user_db.get_user((client_ip, client_port))

            downloaded_size = 0
            logger.info(
                f"User ({client_ip}, {client_port}) using {addr} is uploading file {file_name} size: {f_size} type: {f_type}")
            with open(buffer + file_name, 'wb') as f:
                # todo: add TRY
                data = await reader.read(c_bits)
                while downloaded_size < f_size and data:
                    f.write(data)
                    downloaded_size += len(data)
                    if downloaded_size < f_size:
                        data = await reader.read(c_bits)
            logger.info(
                f"User ({client_ip},{client_port}) using {addr} has uploaded file {file_name} size: {f_size} type: {f_type}")
            await self.send_msg('{} : File uploaded', m_type='notice', to_user=(client_ip, client_port))
            await self.send_msg('{} : has uploaded file {}'.format('{}', file_name), m_type='notice',
                                from_user=(client_ip, client_port))
            self._last_file = f"{f_type} {f_size} {file_name}"
        else:
            writer.write('Init error'.encode())
            await writer.drain()
            writer.close()

    async def _handle_connection_file_server(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        c_bits = 4096
        try:
            data = await reader.read(c_bits)
        except ConnectionResetError:
            writer.close()
        while True:
            try:
                data = data.decode()
                if not data:
                    raise
            except:
                writer.write('Init error'.encode())
                await writer.drain()
                writer.close()
                break
            data = data.split()
            if data[0] == '/f':
                await self._receive_file(reader, writer, data[1:], c_bits=c_bits)
            elif data[0] == '/d':
                await self._send_file(reader, writer, data[1:], c_bits=c_bits)
            else:
                writer.write('Init error'.encode())
                await writer.drain()
                writer.close()
            break

    # todo: Name validation
    async def send_msg(self, msg: str, from_user: Tuple[str, int] = ('Server', 0),
                       to_user: Tuple[str, int] = ('All', 0),
                       m_type='msg'):
        try:
            if to_user == ('All', 0):
                await self._send_msg_to_all(msg, from_user, m_type)
            else:
                await self._send_msg(msg, from_user, to_user, m_type)
        except ConnectionResetError as ex:
            logger.error("Got error: %s", traceback.format_exc())
        except BaseException as ex:
            logger.critical("Uncaught exception: %s", ex) #logging.error(exc_info = True) /  logging.exception()

    async def _send_msg_to_all(self, msg, from_user: Tuple[str, int], m_type='msg'):
        for user in self._user_db.get_all_users():
            if user != from_user:
                await self._send_msg(msg, from_user, user, m_type)

    async def _send_msg(self, msg: str, from_user: Tuple[str, int], to_user: Tuple[str, int], m_type='msg'):
        if from_user in self._user_db.get_all_users():
            name = self._user_db.get_user(from_user).name
        else:
            name = from_user[0]
        if m_type == 'msg':
            f_msg = f'{name} >> {msg}'
        elif m_type == 'notice':
            f_msg = msg.format(name)
        else:
            logger.critical('Unknown m_type: %s' % m_type)
            f_msg = ''
        await self._r_send_msg(f_msg.encode(), to_user)

    async def _r_send_msg(self, msg: bytes, to_user: Tuple[str, int]):
        writer: asyncio.StreamWriter = self._user_db.get_writer(to_user)
        try:
            writer.write(msg)
            await writer.drain()
        except ConnectionResetError as ex:
            logger.info("User has lost connection: %s", ex)
            await self._u_exit(to_user)

    async def input_console(self):
        while True:
            message = await self._loop.run_in_executor(None, input)
            logger.info('Got from console: {}'.format(message))
            # todo: Make commands & commands_handler

    def start(self):
        logger.info('Starting server')
        try:
            self._loop = asyncio.get_event_loop()

            # Create server for messages
            coro_chat = asyncio.start_server(self._handle_connection, self._ip_server, self._port_server,
                                             loop=self._loop)
            self._server: asyncio.AbstractServer = self._loop.run_until_complete(coro_chat)

            # Create server for accepting files
            coro_files = asyncio.start_server(self._handle_connection_file_server, self._ip_server,
                                              self._port_server_file, loop=self._loop)
            self._file_server = self._loop.run_until_complete(coro_files)
            # Create server input
            self._loop.create_task(self.input_console())
            logger.info('Serving on {}'.format(self._server.sockets[0].getsockname()))
            self._loop.run_forever()
        except KeyboardInterrupt:
            pass
        except:
            logger.critical("Uncaught exception: %s", traceback.format_exc())

        # Close the server
        self._server.close()
        self._file_server.close()
        self._loop.run_until_complete(self._server.wait_closed())
        self._loop.run_until_complete(self._file_server.wait_closed())
        self._loop.close()


# todo: Noticcer new class

if __name__ == '__main__':
    server = ChatServer(IP, PORT, PORT_FILES)
    server.start()
