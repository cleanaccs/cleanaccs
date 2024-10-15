import json
import string
from enum import Enum


class ScanDataType(Enum):
    TG_USER_NAME = 1
    TG_USERNAME = 2
    TG_ID = 3
    TG_URL = 5
    INSTAGRAM_NAME = 6
    INSTAGRAM_USERNAME = 7
    YOUTUBE_NAME = 8
    YOUTUBE_URL = 9
    NAME = 10
    TG_KEYWORD = 11

    @classmethod
    def from_str(cls, value):
        """Converts a string or integer back to a ScanDataType enum."""
        if isinstance(value, int):
            return cls(value)
        return cls[value]

    def to_str(self):
        """Converts an enum to its string name."""
        return self.name

class ScanData:
    def __init__(self, data: string, data_type: ScanDataType):
        try:
            if data[0] == '@':
                data = data[1:]
        except IndexError:
            pass
        self.data = data.lower()
        self.data_type = data_type

    def to_dict(self):
        return {
            'data': self.data,
            'data_type': self.data_type.to_str()
        }

    @classmethod
    def from_dict(cls, data):
        instance = cls.__new__(cls)
        instance.data = data['data']
        instance.data_type = ScanDataType.from_str(data['data_type'])
        return instance

    def __str__(self):
        return f"{{data={self.data}, data_type={self.data_type}}}"

    def to_str(self):
        return f"{self.data} ({self.data_type.to_str()})"


def load_unwanted_materials(file_path: str) -> list[ScanData]:
    with open(file_path, 'r') as file:
        data = json.load(file)
        return [ScanData.from_dict(channel) for channel in data]
