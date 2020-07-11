import asyncio
from aiopg.sa import create_engine
import sqlalchemy as sa
import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, TIMESTAMP
from sqlalchemy.sql.ddl import CreateTable
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


def create_connection(func):
    # print(f"Got {func}")

    # async def decorator(func):
    async def inner_decor(*args, **kwargs):
        async with create_engine(user='postgres',
                                 database='test_DB',
                                 host='127.0.0.1',
                                 password='123456789') as engine:
            async with engine.acquire() as conn:
                return await func(args[0], conn, args[1:], **kwargs)

    return inner_decor

    # return decorator


class DB_connection():
    def __init__(self):
        metadata = sa.MetaData()
        self.Users = sa.Table('users', metadata, Column('id', Integer, primary_key=True, autoincrement=True),
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

    @create_connection
    async def create_table(self, conn, *args):
        await conn.execute('DROP TABLE IF EXISTS users')
        await conn.execute('DROP TABLE IF EXISTS user_changes')
        await conn.execute(CreateTable(self.UserCharges))
        print('Create UserChanges')
        await conn.execute(CreateTable(self.Users))
        print('Create Users')

    @create_connection
    async def test(self, conn, *args):
        # await self.create_table(conn)
        # await conn.execute(self.Users.insert().values(login='Cat', password='FisH', ))
        # out2=await conn.execute(sa.select([Users.c.id, Users.c.login]).select_from(Users))
        async for res in conn.execute(
                sa.select([self.Users.c.id, self.Users.c.login, self.Users.c.password]).select_from(self.Users)):
            # .where(self.Users.c.id == 1)):
            print(res.id, res.login, res.password)
        print('Complete')

    @create_connection
    async def add_value_to_user(self, conn, *args, **kwargs):
        await conn.execute(self.Users.insert().values(**kwargs))

    async def add_user(self, login, password, nickname=None):
        await self.add_value_to_user(login=login, password=password, nickname=nickname)

    async def test_connection(self):
        login = reduce(lambda a, x: a + x,
                       random.choices(ascii_letters + digits + punctuation, k=random.randint(3, 20)))
        password = reduce(lambda a, x: a + x,
                          random.choices(ascii_letters + digits + punctuation, k=random.randint(3, 20)))
        nickname = reduce(lambda a, x: a + x,
                          random.choices(ascii_letters + digits + punctuation, k=random.randint(3, 20)))
        await self.add_user(login=login, password=password, nickname=nickname)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    database = DB_connection()
    loop.run_until_complete(database.test())
