import json
import string
from enum import Enum


class MaterialType(Enum):
    TG_NAME = 1
    TG_USERNAME = 2
    TG_ID = 3
    URL = 5
    INSTAGRAM_NAME = 6
    INSTAGRAM_LINK = 7
    YOUTUBE_NAME = 8
    YOUTUBE_LINK = 9
    NAME = 10
    TG_KEYWORD = 11

    @classmethod
    def from_str(cls, value):
        """Converts a string or integer back to a MaterialType enum."""
        if isinstance(value, int):
            return cls(value)
        return cls[value]

    def to_str(self):
        """Converts an enum to its string name."""
        return self.name

class UnwantedMaterial:
    def __init__(self, material: string, source: MaterialType):
        try:
            if material[0] == '@':
                material = material[1:]
        except IndexError:
            pass
        self.material = material.lower()
        self.source = source

    def to_dict(self):
        return {
            'material': self.material,
            'source': self.source.to_str()
        }

    @classmethod
    def from_dict(cls, data):
        instance = cls.__new__(cls)
        instance.material = data['material']
        instance.source = MaterialType.from_str(data['source'])
        return instance

    def __str__(self):
        return f"{{material={self.material}, source={self.source}}}"

    def to_str(self):
        return f"{self.material} ({self.source.to_str()})"

class UnwantedChannel:
    def __init__(self, names=None, username="N/A", chat_id="N/A"):
        self.names = names if names else []
        self.username = username
        self.chat_id = chat_id

    def to_dict(self):
        return {
            "names": self.names,
            "username": self.username,
            "chat_id": self.chat_id
        }

    @classmethod
    def from_dict(cls, data):
        chat = cls()
        chat.names = data.get("names", [])
        chat.username = data.get("username", "N/A")
        chat.chat_id = data.get("chat_id", "N/A")
        return chat

    def __str__(self):
        return f"{{names={self.names}, username={self.username}, chat_id={self.chat_id}}}"

def load_unwanted_channels(file_path: str) -> list[UnwantedChannel]:
    with open(file_path, 'r') as file:
        data = json.load(file)
        return [UnwantedChannel.from_dict(channel) for channel in data]

def load_unwanted_materials(file_path: str) -> list[UnwantedMaterial]:
    with open(file_path, 'r') as file:
        data = json.load(file)
        return [UnwantedMaterial.from_dict(channel) for channel in data]
