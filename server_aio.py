import socket
import asyncio
import os
from typing import Tuple, Dict, Optional


# todo: create users database
# todo: message types
# todo: commands


class Chat_server():
    def __init__(self, ip, port):
        self._ip_server = ip
        self._port_server = port
        self._users_arr: Dict = dict()
        self._commands_users = {'/e': self._exit_user, '/i': self._info_users, '/n': self._set_name}
        # todo: make database for users
        self._description = '''
        Hi there. This is the Socket Chat
        now there {} users
        commands: {}
        '''

    @staticmethod
    def print_th(text):
        print(text)

    def _add_user(self, addr, r, w):
        self._users_arr[addr] = dict()
        self._users_arr[addr]['name'] = f'{addr[0]} {addr[1]}'
        self._users_arr[addr]['reader'] = r
        self._users_arr[addr]['writer'] = w

    async def _set_name(self, addr, name):
        self._users_arr[addr]['name'] = name
        await self.send_msg(f'Your name is {name}', to_user=addr)

    async def _info_users(self, addr, *args):
        msg = 'Now {} users connected:\n'.format(len(self._users_arr))
        msg += '\n'.join(map(lambda x: str(f"{x[0]} named: {x[1]['name']}"), self._users_arr.items()))
        await self.send_msg(msg, to_user=addr)

    def _del_user(self, addr):
        del self._users_arr[addr]

    def _get_cur_num_users(self):
        return len(self._users_arr)

    async def _exit_user(self, addr, *args):
        writer: asyncio.StreamWriter = self._users_arr[addr]['writer']
        writer.close()
        user_name = self._users_arr[addr]['name']
        await self._loop.run_in_executor(None, self._del_user, addr)
        await self.send_msg(f"User {user_name} exit")

    async def _handle_new_connection(self, addr, reader, writer):
        await self.send_msg(f"User {addr} has connected")
        await self._loop.run_in_executor(None, self._add_user, addr, reader, writer)
        await self.send_msg(self._description.format(self._get_cur_num_users(), ' '.join(self._commands_users.keys())),
                            to_user=addr)

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
            # todo: more exceptions
            if data:
                message = data.decode()
                # todo: Make commands_from_user_handler
                if message[0] == '/':
                    await self._user_commands_handler(message, addr)
                else:
                    print("{} >> {}".format(addr, message))
                    await self.send_msg(message, from_user=addr)

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
        for user in self._users_arr:
            if user != from_user:
                await self._send_msg(msg, from_user, user)

    async def _send_msg(self, msg: str, from_user, to_user):
        writer: asyncio.StreamWriter = self._users_arr[to_user]['writer']
        if from_user in self._users_arr:
            name = self._users_arr[from_user]['name']
        else:
            name = from_user[0]
        f_msg = f'{name} >> {msg}'
        writer.write(f_msg.encode())
        await writer.drain()

    async def input_concule(self):
        while True:
            message = await self._loop.run_in_executor(None, input)
            print('Got from concole: {}'.format(message))
            # todo: Make commands & commands_handler

    def start(self):
        self._loop = asyncio.get_event_loop()
        coro = asyncio.start_server(self._handle_connection, self._ip_server, self._port_server, loop=self._loop)
        self._server: asyncio.AbstractServer = self._loop.run_until_complete(coro)
        self._loop.create_task(self.input_concule())
        print('Serving on {}'.format(self._server.sockets[0].getsockname()))
        try:
            self._loop.run_forever()
        except KeyboardInterrupt:
            pass

        # Close the server
        self._server.close()
        self._loop.run_until_complete(self._server.wait_closed())
        self._loop.close()


if __name__ == '__main__':
    # main()
    server = Chat_server("127.0.0.1", 10001)
    server.start()
