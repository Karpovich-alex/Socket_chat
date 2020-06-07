import asyncio
from typing import Tuple
from User_data_base.UserDB import UserDB
from tools.config import IP, PORT
import tools.logger_example
import logging
import traceback
from tools.commands import CommandARCH, Command
import pickle

# todo: command_handler
# todo: user login timeout
# todo: command server class
logger = logging.getLogger("tools.logger_example.server")
buffer = 'buffer/'


class Chat_server():
    def __init__(self, ip, port):
        self._ip_server = ip
        self._port_server = port
        self._user_db: UserDB = UserDB()
        self._commands_users = {'/e': self._u_exit, '/i': self._u_info, '/n': self._u_set_name,
                                '/f': self._reciece_file, '/d': self._u_send_file}
        # todo: new description
        self._description = '''
        Hi there. This is the Socket Chat
        now there {} users
        commands: {}
        '''
        self._last_file = '/img 25405 cat.jpg'
        # self._server_commands = CommandARCH('Server')
        try:
            self._loop = asyncio.get_event_loop()
            coro = asyncio.start_server(self._handle_connection, self._ip_server, self._port_server, loop=self._loop)
            self._server: asyncio.AbstractServer = self._loop.run_until_complete(coro)
            self._loop.create_task(self.input_consule())
            logger.info('Serving on {}'.format(self._server.sockets[0].getsockname()))
        except:
            logger.critical("Uncaught exception: %s", traceback.format_exc())

    def _set_commands(self):
        with CommandARCH('Users') as self._user_commands:
            self._user_commands.add_commands(
                Command('exit user', '/e', self._u_exit, description="Exit from server", scope='Server'))
            self._user_commands.add_commands(
                Command('info', '/i', self._u_info, description="View info", scope='Server'))
            self._user_commands.add_commands(
                Command('name', '/n', self._u_set_name, description="Change your name", scope='Server'))
            self._user_commands.add_commands(Command('Acpt file', '/f', self._recieve_file))
            self._user_commands.add_commands(Command('Send file', '/d', self._u_send_file))

    @staticmethod
    def print_th(text):
        print(text)

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
                    print('send')
                    await self._r_send_msg(line, addr)
                    line = f.read(1024)
            await self.send_msg(f"file {file_name} has downloaded", to_user=addr)
            logger.info(f"User {addr} received {file_name}")

        else:
            await self.send_msg(f"Can't find last file", to_user=addr)

    async def _u_set_name(self, addr, *name):
        if name:
            [name] = name
            await self._user_db.set_name(addr, name)
            await self.send_msg(f'Your name is {name}', to_user=addr)
        else:
            await self.send_msg(f"You can't be named ' '", to_user=addr)

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
        logger.info(f"User {user.name} exit")

    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
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
                if message[0] == '/':
                    await self._user_commands_handler(message, addr)
                else:
                    await self.send_msg(message, from_user=addr)
        if addr in self._user_db.get_all_users():
            await self._u_exit(addr)

    async def _handle_new_connection(self, addr, reader, writer):
        logger.info(f"User {addr} has connected")
        await self._user_db.add_user(addr, reader, writer)
        await self.send_msg(
            self._description.format(self._user_db.get_num_users(), ' '.join(self._commands_users.keys())),
            to_user=addr)

    async def _user_commands_handler(self, command: str, addr: Tuple):
        commands = command.split(' ', maxsplit=1)
        command = commands[0]
        if command in self._commands_users:
            com = self._commands_users[command]
            await com(addr, *commands[1:])
        else:
            await self.send_msg('Unsupported command', to_user=addr)

    async def _recieve_file(self, addr, *args):
        # todo: change file_name
        f_type, f_size, file_name = args[0].split()
        self._last_file = f"{f_type} {f_size} {file_name}"
        f_size = int(f_size)
        user = self._user_db.get_user(addr)
        # writer: asyncio.StreamWriter = user.writer
        reader: asyncio.StreamReader = user.reader
        downloaded_size = 0
        logger.info(f"User {addr} uploaded file {file_name} size: {f_size} type: {f_type}")
        with open(buffer + file_name, 'wb') as f:
            # todo: add TRY
            data = await reader.read(1024)
            while downloaded_size < f_size and data:
                f.write(data)
                downloaded_size += len(data)
                if downloaded_size < f_size:
                    data = await reader.read(1024)
        logger.info(f"User {addr} has uploaded file {file_name} size: {f_size} type: {f_type}")
        await self.send_msg('File uploaded', to_user=addr)
        await self._send_msg_to_all(' ', addr, m_type='uploaded_photo')

    # todo: ???
    async def _disconnect_user(self, addr):
        writer: asyncio.StreamWriter = self._user_db.get_writer(addr)
        writer.close()
        await self._u_exit(addr)

    async def send_msg(self, msg: str, from_user: Tuple = ('Server',), to_user: Tuple = ('All',), m_type='msg'):
        try:
            if to_user == ('All',):
                await self._send_msg_to_all(msg, from_user, m_type)
            else:
                await self._send_msg(msg, from_user, to_user, m_type)
        except ConnectionResetError as ex:
            logger.error("Got error: %s", traceback.format_exc())
        except BaseException as ex:
            logger.critical("Uncaught exception: %s", ex)

    async def _send_msg_to_all(self, msg, from_user: Tuple, m_type='msg'):
        for user in self._user_db.get_all_users():
            if user != from_user:
                await self._send_msg(msg, from_user, user, m_type)

    async def _send_msg(self, msg: str, from_user, to_user, m_type='msg'):
        writer: asyncio.StreamWriter = self._user_db.get_writer(to_user)
        if from_user in self._user_db.get_all_users():
            name = self._user_db.get_user(from_user).name
        else:
            name = from_user[0]
        if m_type == 'msg':
            f_msg = f'{name} >> {msg}'
        elif m_type == 'uploaded_photo':
            f_msg = f'User {name} has uploaded photo'
        else:
            logger.critical('Unknown m_type: %s' % m_type)
            f_msg = ''
        await self._r_send_msg(f_msg.encode(), to_user)

    async def _r_send_msg(self, msg: bytes, to_user):
        writer: asyncio.StreamWriter = self._user_db.get_writer(to_user)
        try:
            writer.write(msg)
            await writer.drain()
        except ConnectionResetError as ex:
            logger.info("User has lost connection: %s", ex)
            await self._u_exit(to_user)

    async def input_consule(self):
        while True:
            message = await self._loop.run_in_executor(None, input)
            logger.info('Got from concole: {}'.format(message))
            # todo: Make commands & commands_handler

    def start(self):
        logger.info('Starting server')
        try:
            self._loop.run_forever()
        except KeyboardInterrupt:
            pass

        # Close the server
        self._server.close()
        self._loop.run_until_complete(self._server.wait_closed())
        self._loop.close()


if __name__ == '__main__':
    server = Chat_server(IP, PORT)
    server.start()
