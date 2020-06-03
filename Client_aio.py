import socket
import asyncio
import os
from concurrent.futures import FIRST_COMPLETED
import traceback


# todo: принимать сообщения сервер
# todo: Fix this!!

class Client:
    def __init__(self, server_info):
        self._server_ip, self._server_port = server_info

    async def _create_com(self):
        self._reader, self._writer = await asyncio.open_connection("127.0.0.1", 10001)
        self._addr = self._writer.get_extra_info("sockname")
        self.print_th('Your ip: {}'.format(self._addr))
        # await self._send_msg(reader,writer,addr,loop)
        # await self._recieve_msg(reader,writer,addr,loop)
        futures = [self._send_msg(), self._recieve_msg()]
        done, pending = await asyncio.wait(futures, return_when=FIRST_COMPLETED)
        self.print_th(done.pop().result())
        for future in pending:
            future.cancel()

    async def _recieve_msg(self):
        while True and not asyncio.tasks.Task.cancelled(self._writer.current_task()):
            try:
                print(asyncio.current_task())
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

    async def _send_msg(self):
        while True:
            try:
                message = await self._loop.run_in_executor(None, input)
                if message.lower() == '/e':
                    self._writer.close()
                    self.stop('Closed by console')
                    # asyncio.tasks.Task.done(asyncio.current_task())
                    return 'Closing Connection'
                else:
                    self._writer.write(message.encode())
                    await self._writer.drain()

            except asyncio.CancelledError:
                self._writer.close()
                # asyncio.tasks.Task.done(asyncio.current_task())
                return 'CancelledError'
            except asyncio.TimeoutError as error:
                self.print_th(f'{self._addr}: WEBSOCKET_TIMEOUT: {error}')
                self._writer.close()
                # asyncio.tasks.Task.done(asyncio.current_task())
                return 'Connection is closed'

    @staticmethod
    def print_th(text):
        print(text)

    def stop(self, msg):
        # self._loop.close()
        asyncio.tasks.Task.cancel(asyncio.current_task())
        self.print_th(msg)

    def start(self):
        self._loop = asyncio.get_event_loop()
        try:
            self._loop.run_until_complete(self._create_com())
        except ConnectionRefusedError as error:
            self.print_th(f': WEBSOCKET_TIMEOUT: {error}')
        else:
            self.print_th(f'Unexpected error: {traceback.format_exc()}')
        finally:
            self._loop.close()
            self.print_th('Your connection is closed')


if __name__ == '__main__':
    server_adress = ("127.0.0.1", 10001)
    client = Client(server_adress)
    client.start()
