from tools.message.message import DataContainer


class MessageParser:
    """
    Helps Server handle messages and assign data_type with function
    """
    def __init__(self):
        self._message_types = dict()
    def add_action(self, name, *functions, parent_commands=''):
        pass