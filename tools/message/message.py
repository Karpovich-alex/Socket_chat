from time import time
import json
import pickle


class Message:
    def __init__(self, from_user=None, to_user=None, m_type=None, m_content=None,
                 **kwargs):
        """
        Create a message instance which helps to communicate client with server
        :param from_user:
        :param to_user:
        :param m_type:
        :param m_content:
        :param kwargs:
        """
        self.m_type = m_type
        self.from_user = from_user
        self.to_user = to_user
        self.content = m_content
        self.m_created_time = time()
        # self.m_send_time = None
        for name, value in kwargs.items():
            self.__setattr__(name, value)

    def dump_to_json(self):
        return json.dumps(self.__dict__)

    def to_binary(self):
        # self.m_send_time = time()
        return pickle.dumps(self.dump_to_json())

    @classmethod
    def load_from_json(cls, json_file):
        dict_json = json.loads(json_file)
        return cls(**dict_json)

    @classmethod
    def from_binary(cls, binary_json):
        simple_json = pickle.loads(binary_json)
        return cls.load_from_json(simple_json)


if __name__ == "__main__":
    m = Message('alex', 'lol', 'text', 'Hi there', kwarg='lolesh')
    print(m.dump_to_json())
    print(m.to_binary())
    json_data = (
        '{"m_type": "text", "from_user": "alex", "to_user": "lol", "content": "Hi there", "m_created_time": 1593537484.939852, "kwarg": "lolesh"}')
    print(Message.load_from_json(json_data).dump_to_json())
