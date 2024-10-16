import os
import string
from enum import Enum
import glob

from cleanup.config.scan_config import load_config, Config


class ScanDataType(Enum):
    TG_USER_NAME = 1
    TG_USERNAME = 2
    TG_ID = 3
    TG_KEYWORD = 4
    TG_URL = 5
    INSTAGRAM_NAME = 6
    INSTAGRAM_USERNAME = 7
    INSTAGRAM_URL = 8
    YOUTUBE_NAME = 9
    YOUTUBE_URL = 10
    TG_IGNORED_ID = 11

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


def load_scan_data(config: Config) -> list[ScanData]:
    scan_data_dir = config.paths.scan_data_dir
    suffixes = config.paths.scan_data_suffixes

    data_files = {
        ScanDataType.TG_ID: suffixes.telegram_ids,
        ScanDataType.TG_USER_NAME: suffixes.telegram_user_names,
        ScanDataType.TG_USERNAME: suffixes.telegram_usernames,
        ScanDataType.TG_KEYWORD: suffixes.telegram_keywords,
        ScanDataType.TG_URL: suffixes.telegram_urls,
        ScanDataType.INSTAGRAM_USERNAME: suffixes.instagram_usernames,
        ScanDataType.INSTAGRAM_URL: suffixes.instagram_urls,
        ScanDataType.INSTAGRAM_NAME: suffixes.instagram_names
    }

    scan_data = []

    for data_type, suffix in data_files.items():
        pattern = os.path.join(scan_data_dir, f"*{suffix}")
        for file_path in glob.glob(pattern):
            with open(file_path, 'r') as file:
                for line in file:
                    data = line.strip()
                    if data:
                        scan_data.append(ScanData(data, data_type))

    return scan_data

if __name__ == "__main__":
    config, config_exists = load_config("config.yaml")
    scan_data = load_scan_data(config)
    for material in scan_data:
        print(material)
