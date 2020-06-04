from typing import Dict
from User_data_base.User import User
from asyncio import StreamWriter, StreamReader


class UserDB:
    def __init__(self):
        self._users_arr: Dict = dict()
        self._count_users: int = 0

    async def add_user(self, addr, r, w):
        self._users_arr[addr] = User(addr, r, w)
        self._count_users += 1

    async def set_name(self, addr, name):
        self._users_arr[addr].name = name

    def get_all_users(self):
        return self._users_arr.keys() or []

    def info_users(self):
        msg = 'Now {} users connected:\n'.format(self._count_users)
        msg += '\n'.join(map(lambda x: str(f"{x.addr} named: {x.name}"), self))
        return msg

    def del_user(self, addr):
        del self._users_arr[addr]

    def get_user(self, addr) -> User:
        return self._users_arr[addr]

    def get_writer(self, addr) -> StreamWriter:
        user = self.get_user(addr)
        return user.writer

    def get_reader(self, addr) -> StreamReader:
        user = self.get_user(addr)
        return user.reader

    def get_num_users(self):
        return self._count_users

    def __iter__(self):
        for user in self._users_arr.values():
            yield user
