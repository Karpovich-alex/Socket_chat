import asyncio
from typing import Tuple, Dict
from User_data_base.User import User
from User_data_base.UserDB import UserDB


# todo: create users database
# todo: message types
# todo: commands


class Chat_server():
    def __init__(self, ip, port):
        self._ip_server = ip
        self._port_server = port
        self._user_db: UserDB = UserDB()
        self._commands_users = {'/e': self._exit_user, '/i': self._info_users, '/n': self._set_name,
                                '/inform': self._info_users}
        self._description = '''
        Hi there. This is the Socket Chat
        now there {} users
        commands: {}
        '''
        self._loop = asyncio.get_event_loop()
        coro = asyncio.start_server(self._handle_connection, self._ip_server, self._port_server, loop=self._loop)
        self._server: asyncio.AbstractServer = self._loop.run_until_complete(coro)
        self._loop.create_task(self.input_consule())
        self.print_th('Serving on {}'.format(self._server.sockets[0].getsockname()))

    @staticmethod
    def print_th(text):
        print(text)

    async def _infor(self, addr, *args):
        msg = ' '.join(map(lambda x: f"{x[0]} {x[1]}", self._user_db._users_arr.keys()))
        await self.send_msg(msg, to_user=addr)

    async def _set_name(self, addr, name):
        await self._user_db.set_name(addr, name)
        await self.send_msg(f'Your name is {name}', to_user=addr)

    async def _info_users(self, addr, *args):
        msg = self._user_db.info_users()
        await self.send_msg(msg, to_user=addr)

    async def _exit_user(self, addr, *args):
        user = self._user_db.get_user(addr)
        writer: asyncio.StreamWriter = user.writer
        writer.close()
        await self._loop.run_in_executor(None, self._user_db.del_user, addr)
        await self.send_msg(f"User {user.name} exit")

    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info("peername")
        await self._handle_new_connection(addr, reader, writer)
        while True:
            try:
                data = await reader.read(1024)
            except ConnectionResetError:
                await self._exit_user(addr)
                break
            except asyncio.TimeoutError as error:
                print(f'{addr}: WEBSOCKET_TIMEOUT: {error}')
                writer.close()
                break
            else:
                pass
            # todo: more exceptions
            if data:
                message = data.decode()
                # todo: Make commands_from_user_handler
                if message[0] == '/':
                    await self._user_commands_handler(message, addr)
                else:
                    print("{} >> {}".format(addr, message))
                    await self.send_msg(message, from_user=addr)

    async def _handle_new_connection(self, addr, reader, writer):
        await self.send_msg(f"User {addr} has connected")
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

    async def send_msg(self, msg: str, from_user: Tuple = ('Server',), to_user: Tuple = ('All',)):
        if to_user == ('All',):
            await self._send_msg_to_all(msg, from_user)
        else:
            await self._send_msg(msg, from_user, to_user)

    async def _send_msg_to_all(self, msg, from_user: Tuple):
        for user in self._user_db.get_all_users():
            if user != from_user:
                await self._send_msg(msg, from_user, user)

    async def _send_msg(self, msg: str, from_user, to_user):
        writer: asyncio.StreamWriter = self._user_db.get_writer(to_user)
        if from_user in self._user_db.get_all_users():
            name = self._user_db.get_user(from_user).name
        else:
            name = from_user[0]
        f_msg = f'{name} >> {msg}'
        writer.write(f_msg.encode())
        await writer.drain()

    async def input_consule(self):
        while True:
            message = await self._loop.run_in_executor(None, input)
            print('Got from concole: {}'.format(message))
            # todo: Make commands & commands_handler

    def start(self):
        self.print_th('Starting server')
        try:
            self._loop.run_forever()
        except KeyboardInterrupt:
            pass

        # Close the server
        self._server.close()
        self._loop.run_until_complete(self._server.wait_closed())
        self._loop.close()


if __name__ == '__main__':
    server = Chat_server("127.0.0.1", 10001)
    server.start()
