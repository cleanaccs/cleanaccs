import os
import string
from enum import Enum
import glob
from typing import Tuple, List, Dict, Any

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


class ScanDataEntry:
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


class ScanData:
    def __init__(self, config: Config):
        self.config = config
        self.data: list[ScanDataEntry] = []
        self.data_by_type: dict[ScanDataType, list[ScanDataEntry]] = {}


    def __load_scan_data(self) -> tuple[list[ScanDataEntry], dict[ScanDataType, list[ScanDataEntry]]]:
        scan_data_dir = self.config.paths.scan_data_dir
        suffixes = self.config.paths.scan_data_suffixes

        data_files = {
            ScanDataType.TG_ID: suffixes.telegram_ids,
            ScanDataType.TG_USER_NAME: suffixes.telegram_user_names,
            ScanDataType.TG_USERNAME: suffixes.telegram_usernames,
            ScanDataType.TG_KEYWORD: suffixes.telegram_keywords,
            ScanDataType.TG_URL: suffixes.telegram_urls,
            ScanDataType.TG_IGNORED_ID: suffixes.telegram_ignored_ids,
            ScanDataType.INSTAGRAM_USERNAME: suffixes.instagram_usernames,
            ScanDataType.INSTAGRAM_URL: suffixes.instagram_urls,
            ScanDataType.INSTAGRAM_NAME: suffixes.instagram_names
        }

        scan_data_entries = []
        scan_data_by_type = {
            ScanDataType.TG_ID: [],
            ScanDataType.TG_USER_NAME: [],
            ScanDataType.TG_USERNAME: [],
            ScanDataType.TG_KEYWORD: [],
            ScanDataType.TG_URL: [],
            ScanDataType.TG_IGNORED_ID: [],
            ScanDataType.INSTAGRAM_USERNAME: [],
            ScanDataType.INSTAGRAM_URL: [],
            ScanDataType.INSTAGRAM_NAME: [],
        }

        for data_type, suffix in data_files.items():
            pattern = os.path.join(scan_data_dir, f"*{suffix}")
            for file_path in glob.glob(pattern):
                with open(file_path, 'r') as file:
                    for line in file:
                        data = line.strip()
                        if data:
                            entry = ScanDataEntry(data, data_type)
                            scan_data_entries.append(entry)
                            scan_data_by_type[data_type].append(entry)

        return scan_data_entries, scan_data_by_type

    def load(self):
        self.data, self.data_by_type = self.__load_scan_data()
        return self


if __name__ == "__main__":
    config, config_exists = load_config("config.yaml")
    scan_data = ScanData(config)
    for material in scan_data.data:
        print(material)
