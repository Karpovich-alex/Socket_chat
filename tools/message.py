from time import time
import json


class Message:
    def __init__(self, from_user=None, to_user=None, m_type=None, m_content=None,
                 **kwargs):
        self.m_type = m_type
        self.from_user = from_user
        self.to_user = to_user
        self.content = m_content
        self.m_created_time = time()
        for name, value in kwargs.items():
            self.__setattr__(name, value)

    def dump_to_json(self):
        return json.dumps(self.__dict__)

    @classmethod
    def load_from_json(cls, json_file):
        dict_json = json.loads(json_file)
        return cls(**dict_json)


if __name__ == "__main__":
    m = Message('alex', 'lol', 'text', 'Hi there', kwarg='lolesh')
    print(m.dump_to_json())
    json_data = (
        '{"m_type": "text", "from_user": "alex", "to_user": "lol", "content": "Hi there", "m_created_time": 1593537484.939852, "kwarg": "lolesh"}')
    print(Message.load_from_json(json_data).dump_to_json())
