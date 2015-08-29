#!/usr/bin/python3

from collections import namedtuple, defaultdict
from collections import namedtuple
from os import getcwd, chdir
import sqlite3


try:
    import click

except ImportError as ex:
    raise ImportError("Please install click via pip") from ex


COL_SQL = "PRAGMA table_info(Messages);"
MSG_SQL = "select * from Messages;"


class Message(namedtuple('Message', 'user msg')):
    def __str__(self):
        return ': '.join((str(self.user), str(self.msg)))


class Chat(namedtuple('Chat', 'users msgs id')):
    def __new__(cls, msgs: iter, id: int=None):
        users = sorted({msg.user for msg in msgs})

        return super().__new__(cls, users, msgs, id)

    def __str__(self):
        return '\n'.join(map(str, self))

    def __repr__(self):
        return "<Chat #%s with %s messages by %s>" % \
            (self.id if self.id else '?',
             len(self.msgs),
             ', '.join(self.users))

    def __cmp__(self, other):
        if not isinstance(other, Chat) or \
             self.id is None or \
             other.id is None:

            return super().__cmp__(other)

        elif self.id < other.id:
            return -1

        elif self.id == other.id:
            return 0

        elif self.id > other.id:
            return 1

    def __hash__(self):
        return hash(str(self)) if self.id is None else self.id

    def __iter__(self):
        return iter(self.msgs)

    def save(self, filename: str=None, max_length=60) -> str:
        users = '_'.join(self.users)
        filename = (filename if filename else "chat_%s_%s" % (hash(self), users))[:max_length] + '.txt'
        
        with open(filename, 'w') as file:
            file.write(str(self))

        return filename

def get_skype_map(path: str) -> dict:
    skype_map = defaultdict(list)

    with sqlite3.connect(path) as connection:
        cursor = connection.cursor()
        col_info = cursor.execute(COL_SQL)
        fields = (info[1] for info in col_info.fetchall())
        Row = namedtuple("Row", fields)
        
        rows = cursor.execute(MSG_SQL).fetchall()

        for row in rows:
            row = Row(*row)
            skype_map[row.convo_id].append(row)

    return skype_map

def get_skype_chats(path: str) -> iter:
    skype_map = get_skype_map(path)

    for chat_id, msgs in skype_map.items():
        msg_objs = tuple(Message(row.author, row.body_xml) 
                         for row in msgs)

        yield Chat(msg_objs, chat_id)

@click.command()
@click.option("-s", "--save", default='.', help="Path to save chats")
@click.argument("file")
def chats_to_files(file: str=None, save: str='.'):
    if not file:
        raise ValueError("Skype main.db not found")

    cwd = getcwd()
    chdir(save)

    for chat in get_skype_chats(file):
        print(chat.save())

    print("Files saved to %s" % save)

    chdir(cwd)

if __name__ == "__main__":
    chats_to_files()
