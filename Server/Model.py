import asyncio
from aiopg.sa import create_engine
import sqlalchemy as sa
import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, TIMESTAMP
from sqlalchemy.sql.ddl import CreateTable
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from functools import reduce
import random
from string import ascii_letters, punctuation, digits
from typing import Tuple
import time


class DataBaseCreator:

    def __init__(self):
        """
        Create tables
        """
        metadata = sa.MetaData()
        self.Users = sa.Table('users', metadata,
                              Column('id', Integer, primary_key=True, autoincrement=True),
                              Column('login', String(100), nullable=False),
                              Column('password', String(100), nullable=False),
                              Column('nickname', String(100)),
                              Column('last_update_id', Integer, ForeignKey("user_changes.id")))

        self.UserCharges = sa.Table('user_changes', metadata,
                                    Column('id', Integer, primary_key=True, autoincrement=True),
                                    Column('time_update', TIMESTAMP),
                                    Column('type_update', String(100)),
                                    Column('update_content', String(250)),
                                    Column('past_update_id', Integer, default=-1))

        self.Sessions = sa.Table('session_list', metadata,
                                 Column('id', Integer, primary_key=True, autoincrement=True),
                                 Column('User_id', Integer, ForeignKey("users.id")),
                                 Column('ip', String(15)),
                                 Column('port', Integer),
                                 Column('time_connected', TIMESTAMP),
                                 Column('time_disconnected', TIMESTAMP, default=0),
                                 Column('is_connected', sa.Boolean))

        self.FilesInfo = sa.Table('files_info', metadata,
                                  Column('id', Integer, primary_key=True, autoincrement=True),
                                  Column('from_user', Integer, ForeignKey("users.id")),
                                  Column('file_type', Integer),
                                  Column('time_created', TIMESTAMP),
                                  Column('file_path', String(100)))

        self.Message = sa.Table('messages', metadata,
                                Column('id', Integer, primary_key=True, autoincrement=True),
                                Column('from_user', Integer, ForeignKey('users.id')),
                                Column('to_user', Integer, ForeignKey('users.id')),
                                Column('time', TIMESTAMP),
                                Column('message_type', String(30)),
                                Column('message_text', String(250)),
                                Column('content_id', Integer, ForeignKey('files_info.id'), default=-1))
        self.engine = None

    def create_connection(self, func):
        """
        Decorator which helps work with db connection
        :param func:
        :return:
        """
        async def inner_decor(*args, **kwargs):
            async with self.engine.acquire() as conn:
                try:
                    return await func(args[0], conn, **kwargs)
                except Exception as e:
                    print(e)
                    return 0

        return inner_decor

    async def create_data_base(self, drop_table=False):
        """
        Create tables if they not exist
        :return:
        """
        if drop_table:
            async with self.engine.acquire() as conn:
                await conn.execute('DROP TABLE IF EXISTS user_changes CASCADE')
                await conn.execute('DROP TABLE IF EXISTS users CASCADE')
                await conn.execute('DROP TABLE IF EXISTS user_changes')
                await conn.execute('DROP TABLE IF EXISTS session_list CASCADE')
                await conn.execute('DROP TABLE IF EXISTS files_info CASCADE')
                await conn.execute('DROP TABLE IF EXISTS messages CASCADE')
                await conn.execute(CreateTable(self.UserCharges))
                await conn.execute(CreateTable(self.Users))
                await conn.execute(CreateTable(self.Sessions))
                await conn.execute(CreateTable(self.FilesInfo))
                await conn.execute(CreateTable(self.Message))

    async def prepare(self):
        self.engine = await create_engine(user='postgres',
                                          database='test_DB',
                                          host='127.0.0.1',
                                          password='Testpass')

    async def close_connection(self):
        await self.engine.close()


class DataBaseConnection:
    database = DataBaseCreator()

    def __init__(self, create_new_data_base=False):
        # await self.database.create_data_base()
        pass

    async def prepare(self):
        await self.database.prepare()

    async def create_db(self):
        await self.database.create_data_base()

    async def close_connection(self):
        await self.database.close_connection()

    @database.create_connection
    async def add_user(self, conn, login: str, password: str, nickname=None):
        await conn.execute(self.database.Users.insert().values(login=login, password=password, nickname=nickname))

    @database.create_connection
    async def add_message(self, conn, from_user: int, to_user:  int, message_type: str,
                          message_text: str, content_id: int, message_time=None):
        if not message_time:
            message_time = time.time()
        await conn.execute(
            self.database.Message.insert().values(from_user=from_user, to_user=to_user, message_text=message_text,
                                                  message_time=message_time, message_type=message_type,
                                                  content_id=content_id))

    @database.create_connection
    async def add_session(self, conn, user_id: int, ip: str, port: int, time_connected, time_disconnected,
                          is_connected=False):
        await conn.execute(
            self.database.Sessions.insert().values(user_id=user_id, ip=ip, port=port, time_connected=time_connected,
                                                   time_disconnected=time_disconnected, is_connected=is_connected))

    @database.create_connection
    async def get_user_id(self, conn, addr: Tuple) -> int:
        """
        Takes tuple with ip and port and return id in users table
        :param conn:
        :param addr:
        :return:
        """
        user_ip, user_port = addr
        user_id = await (await conn.execute(sa.select(['id']).select_from('users').where(
            self.database.Users.c.ip == user_ip & self.database.Users.c.port == user_port)).fetch_one())
        print(user_id)
        return user_id

    async def test_connection(self):
        login = reduce(lambda a, x: a + x,
                       random.choices(ascii_letters + digits + punctuation, k=random.randint(3, 20)))
        password = reduce(lambda a, x: a + x,
                          random.choices(ascii_letters + digits + punctuation, k=random.randint(3, 20)))
        nickname = reduce(lambda a, x: a + x,
                          random.choices(ascii_letters + digits + punctuation, k=random.randint(3, 20)))
        await self.add_user(login=login, password=password, nickname=nickname)

    @database.create_connection
    async def test(self, conn, *args):
        # await conn.execute(self.Users.insert().values(login='Cat', password='FisH', ))
        # out2=await conn.execute(sa.select([Users.c.id, Users.c.login]).select_from(Users))
        async for res in conn.execute(
                sa.select([self.database.Users.c.id, self.database.Users.c.login,
                           self.database.Users.c.password]).select_from(self.database.Users)):
            # .where(self.Users.c.id == 1)):
            print(res.id, res.login, res.password)
        print('Complete')


def main():
    loop = asyncio.get_event_loop()
    database = DataBaseConnection(create_new_data_base=True)
    loop.run_until_complete(database.close_connection())


if __name__ == '__main__':
    main()
