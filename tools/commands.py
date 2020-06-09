from typing import Callable, Tuple, Optional


# todo: Cub Command
class Command:
    def __init__(self, name: str, com: str, *actions: Callable, description: str = "", scope: str = 'Client',
                 sub_command: Tuple = (), completer=None):
        self._name = name
        self._com = com
        self._actions = actions or None
        self._description = description
        self._scope = scope
        self._sub_command = sub_command
        self._completer = completer
        if self._sub_command and completer:
            for sub_com in self._sub_command:
                sub_com.set_completer(completer)

    # todo: make output great
    def __repr__(self):
        out = f"{self._com} - {self._description if self._description else self._name}"
        sub_out = ''
        if self._sub_command:
            sub_out = ':\n'
            sub_out += '\n'.join(map(lambda x: "\t" + str(x), self._sub_command))
        return out + sub_out

    def __str__(self):
        return self.__repr__()

    def set_completer(self, compl):
        self._completer = compl

    def get_completer(self):
        sub_dict = dict()
        if self._sub_command:
            for sub_com in self._sub_command:
                sub_dict.update(sub_com.get_completer())
            # return {self._com: dict(lambda x: {x._com : x.get_completer()}, self._sub_command)}
            return {self._com: (self._description, sub_dict)}
        else:
            return {self._com: (self._description, self._completer)}

    async def _do_com(self, *args, **kwargs):
        for func in self._actions:
            await func(*args, **kwargs)

    def get_com(self):
        return self._com

    def get_scope(self):
        return self._scope

    async def __call__(self, *args, **kwargs):
        await self._do_com(*args, **kwargs)


class CommandARCH:
    def __init__(self, name, recovery=None):
        self.name = name
        if recovery:
            pass
        else:
            self._allcom_db = dict()
        # self.info = self._get_info()
        self.info = ""

    def add_commands(self, command: Command):
        self._allcom_db[command.get_com()] = command

    def _add_com_to_db(self):
        pass

    def check_com(self, com):
        return com in self._allcom_db.keys()

    def get_completer(self):
        out_dict = dict()
        for com in self:
            out_dict.update(com.get_completer())
        return out_dict

    def __contains__(self, com):
        return com in self._allcom_db.keys()

    def get_com(self, com):
        return self._allcom_db[com]

    def get_all_coms(self):
        return self._allcom_db.keys() or []

    def _get_info(self):
        return '\n'.join(map(str, self))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.info = self._get_info()

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
    import pickle


    def helper(inp, *args, **kwargs):
        print('help:', inp)
        print(kwargs)


    def shit(*args, **kwargs):
        print('Shit this %s' % kwargs)


    def super(*args, **kwargs):
        return 2 + 1


    # arch_1=CommandARCH('Test')
    with CommandARCH('Test') as arch2:
        new_c = Command('helper', '/h', help, shit, description='Don\'t know')
        arch2.add_commands(new_c)
        arch2.add_commands(Command('Super_comand', '/super', super, description='Just 2+1'))
    print(arch2.info)
    print(arch2)
    print(arch2.get_completer())
    # with open('test.txt', 'wb') as f:
    #     pickle.dump(arch2, f)
    # print(pickle.dumps(arch2))
    # with open('test.txt', 'rb') as f:
    #     a = pickle.load(f)
    # print(a.info)
    # new_c('Hello', name='World')
