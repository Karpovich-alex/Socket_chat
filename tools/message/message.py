from time import time
import json
import pickle
from typing import Tuple


class DataContainer:
    """
    This class is used to be Parent for all messages and data, which will be sending via websockets

    """

    def __init__(self, data_type=None, from_user=None, to_user=None, **kwargs):
        self._data_types = tuple()
        self.data_type = data_type
        self.from_user = from_user
        self.to_user = to_user
        self.created_time = time()
        for name, value in kwargs.items():
            self.__setattr__(name, value)

    @property
    def data_type(self):
        return self._data_types

    @data_type.setter
    def data_type(self, val):
        self._data_types: Tuple = self._data_types + (val,)

    # TODO: add parsing DataContainer class in vars
    def dump_to_json(self):
        return json.dumps(self.__dict__)

    def to_binary(self):
        return pickle.dumps(self.dump_to_json())

    def prepare_message(self, from_user):
        self.from_user = from_user
        return self.to_binary()

    @classmethod
    def load_from_json(cls, json_file):
        dict_json = json.loads(json_file)
        return cls(**dict_json)

    @classmethod
    def from_binary(cls, binary_json):
        simple_json = pickle.loads(binary_json)
        return cls.load_from_json(simple_json)


class MessageContainer(DataContainer):
    """
    A message instance which helps to communicate client with server
    """

    def __init__(self, from_user=None, to_user=None, data_type=None, **kwargs):
        super().__init__(data_type='message', from_user=from_user, to_user=to_user, **kwargs)
        self.data_type = data_type


class Message(MessageContainer):
    def __init__(self, from_user=None, to_user=None, message_type=None, message_text=None,
                 message_attachment: MessageContainer = None, **kwargs):
        super().__init__(data_type='text', to_user=to_user, from_user=from_user, **kwargs)
        self.message_type = message_type
        self.message_text = message_text
        self.message_attachment = message_attachment


class ServiceDataContainer(DataContainer):
    """
    Use to sending information to server
    """

    def __init__(self, data_type=None, **kwargs):
        super().__init__(data_type='service_message', to_user='server')
        self.data_type = data_type


class LoginData(ServiceDataContainer):
    """
    A Login instance using to authentication on server
    use prepare_data method to add from user field
    """

    def __init__(self, login=None, password=None, **kwargs):
        super().__init__(data_type='login_data')
        self.login = login
        self.password = password


class SignInData(ServiceDataContainer):
    def __init__(self, nickname=None, login=None, password=None, **kwargs):
        super().__init__(data_type='sign_in')
        self.nickname = nickname
        self.login = login
        self.password = password


if __name__ == "__main__":
    m = Message('alex', 'lol', 'text', 'Hi there', kwarg='lolesh')
    print(m.dump_to_json())
    print(m.to_binary())
    json_data = (
        '{"m_type": "text", "from_user": "alex", "to_user": "lol", "content": "Hi there", "m_created_time": 1593537484.939852, "kwarg": "lolesh"}')
    print(Message.load_from_json(json_data).dump_to_json())
    print()
    print(LoginData(login='Joshuan', password='Jon20012202').dump_to_json())
