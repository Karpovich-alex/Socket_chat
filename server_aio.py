import socket
import asyncio
import os
from typing import Tuple, Dict


# todo: create users database
# todo: message types
# todo: commands


# conn.settimeout(1)#timeout for connection


class Chat_server():
    def __init__(self, ip, port):
        self._ip_server = ip
        self._port_server = port
        self._users_arr: Dict = dict()

    @staticmethod
    def print_th(text):
        print(text)

    def _add_user(self, addr, r, w):
        self._users_arr[addr] = {'name': addr}
        self._users_arr[addr] = {'reader': r}
        self._users_arr[addr] = {'writer': w}

    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        # data = await reader.read(1024)
        # message = data.decode()
        # addr = writer.get_extra_info('peername')
        # print("Received %r from %r" % (message, addr))
        # writer.close()
        addr = writer.get_extra_info("peername")
        print('{} has connected'.format(addr))
        await self._loop.run_in_executor(None, self._add_user, addr, reader, writer)
        while True:
            # self._add_user(addr)
            # self.print_th('Cur User_arr: {}'.format(self._users_arr))
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
                if message == '/i':
                    print(self._users_arr)
                print("{} >> {}".format(addr, message))
                await self.send_msg_to_all(message, addr)

    async def send_msg_to_all(self, msg, from_user: Tuple):
        for user in self._users_arr:
            if user != from_user:
                await self.send_msg(f'{from_user} >> {msg}', user)

    async def send_msg(self, msg: str, to_user):
        writer: asyncio.StreamWriter = self._users_arr[to_user]['writer']
        writer.write(msg.encode())
        await writer.drain()

    async def input_concule(self):
        while True:
            message = await self._loop.run_in_executor(None, input)
            print('Got from concole: {}'.format(message))

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
