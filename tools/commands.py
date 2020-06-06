from typing import Callable


class Command:
    def __init__(self, name: str, com: str, *actions: Callable, description: str = ""):
        self._name = name
        self._com = com
        self._actions = actions
        self._description = description

    def __repr__(self):
        out = f"{self._com} {'-' if self._description else 'No description :('} {self._description} "
        return out

    def __str__(self):
        return self.__repr__()

    async def _do_com(self, *args, **kwargs):
        for func in self._actions:
            await func(*args, **kwargs)

    def get_com(self):
        return self._com

    async def __call__(self, *args, **kwargs):
        await self._do_com(*args, **kwargs)


class CommandARCH:
    def __init__(self, name, recovery=None):
        self.name = name
        if recovery:
            pass
        else:
            self._allcom_db = dict()

    def add_commands(self, command: Command):
        self._allcom_db[command.get_com()] = command

    def _add_com_to_db(self):
        pass

    def check_com(self, com):
        return com in self._allcom_db.keys()

    def get_com(self, com):
        return self._allcom_db[com]

    def get_all_coms(self):
        return self._allcom_db.keys() or []

    def get_info(self):
        return '\n'.join(map(str,self))
    # todo: Fix this iter(
    def __iter__(self):
        return (com_cls for com_cls in self._allcom_db.values())

    # def __next__(self):
    #     i=0
    #     length=len(self._allcom_db)
    #     for com_cls in self._allcom_db.values():
    #         if i>length:
    #             break
    #         i+=1
    #         yield com_cls
    #     raise StopIteration


# Tests
if __name__ == '__main__':
    def helper(inp, *args, **kwargs):
        print('help:', inp)
        print(kwargs)


    def shit(*args, **kwargs):
        print('Shit this %s' % kwargs)
    arch_1=CommandARCH('Test')
    new_c = Command('helper', '/h', help, shit,description='Don\'t know')
    print(new_c)
    arch_1.add_commands(new_c)
    print(arch_1.get_info())

    new_c('Hello', name='World')

