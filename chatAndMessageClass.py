from datetime import datetime


class Chat:
    def __init__(self, chat_ID, list_members=[], chat_history=[], name=None):
        self.chat_ID = chat_ID  # int, also used for room number
        self.list_members = list_members    # [username]
        self.chat_history = chat_history    # [{sender:, timestamp:, message: }]
        if name is None:
            self.name = ', '.join(list_members)
        else:
            self.name = name

    def get_name(self):
        return self.name

    def get_num_members(self):
        return len(self.list_members)

    def change_name(self, new_name):
        self.name = new_name

    def add_member(self, user_name):
        self.list_members.append(user_name)

    def remove_member(self, user_name):
        self.list_members.remove(user_name)

    def new_message(self, message, sender, time):
        message = Message(message, sender, time)
        self.chat_history.append(message)

    def to_data(self):
        data = {'chat_ID': self.chat_ID, 'chat_name': self.name, 'members': self.list_members}
        return data


class Message:
    def __init__(self, text, sender=None, time=None):
        self.text = text
        self.sender = sender
        self.time = time

    def to_data(self):
        return {'message': self.text, 'sender': self.sender, 'timestamp': self.time.strftime("%H:%M:%S")}
