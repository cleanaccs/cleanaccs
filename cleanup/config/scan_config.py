import re
from typing import Union

import yaml
from datetime import datetime, timedelta, timezone

from cleanup.config.common_flags import EnabledFlag, DeleteFlag, AskFlag

class Config:
    def __init__(self):
        self.paths = PathsConfig()
        self.telegram = TelegramConfig()
        self.instagram = InstagramConfig()

    def __str__(self):
        yaml_str = yaml.dump(self.__dict__, default_flow_style=False, sort_keys=False, indent=2)
        return "\n".join([re.sub(r" ?!!python/.*$", "", l) for l in yaml_str.splitlines()])

class TelegramConfig:
    def __init__(self):
        self.enabled = True
        self.api_id = ""
        self.api_hash = ""
        self.from_date = (datetime.now(timezone.utc) - timedelta(weeks=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        self.to_date = datetime.now(timezone.utc).replace(hour=23, minute=59, second=59, microsecond=999999)
        self.cache_peers = False
        self.cache_messages = False
        self.dialogs = TelegramDialogsConfig()
        self.messages = TelegramMessagesConfig()

class PathsConfig:
    def __init__(self):
        self.cache_dir = ".cache"
        self.scan_data_dir = "scan-data"
        self.scan_data_suffixes = ScanDataSuffixesConfig()

class ScanDataSuffixesConfig:
    def __init__(self):
        self.telegram_ids = "tg-ids.txt"
        self.telegram_user_names = "tg-user-names.txt"
        self.telegram_usernames = "tg-usernames.txt"
        self.telegram_keywords = "tg-keywords.txt"
        self.telegram_urls = "tg-urls.txt"
        self.instagram_usernames = "ig-usernames.txt"
        self.instagram_urls = "ig-urls.txt"
        self.instagram_names = "ig-names.txt"

class InstagramConfig:
    def __init__(self):
        self.enabled = True
        self.data_dir = "instagram-user-data"
        self.checks = InstagramChecksConfig()

class InstagramChecksConfig:
    def __init__(self):
        self.reels_comments = EnabledFlag(enabled=True)
        self.post_comments = EnabledFlag(enabled=True)
        self.comments_likes = EnabledFlag(enabled=True)
        self.post_likes = EnabledFlag(enabled=True)

class TelegramDialogsConfig:
    def __init__(self):
        self.users = TelegramDialogSetting()
        self.chats = TelegramDialogSetting()
        self.channels = TelegramChannelsSetting()
        self.checks = EnabledFlag(enabled=True)


class TelegramMessagesConfig:
    def __init__(self):
        self.enabled = False
        self.delete = False
        self.ask = False
        self.checks = TelegramMessageChecksConfig()

class TelegramDialogSetting(EnabledFlag, AskFlag):
    def __init__(self):
        EnabledFlag.__init__(self)
        AskFlag.__init__(self)


class TelegramChannelsSetting(EnabledFlag, AskFlag):
    def __init__(self):
        EnabledFlag.__init__(self)
        AskFlag.__init__(self)
        self.self_only_after_users_count = None
        self.broadcast = False


class TelegramMessageChecksConfig:
    def __init__(self):
        self.urls = TelegramMessageCheckSetting(enabled=True, delete=True)
        self.forwards = TelegramMessageCheckSetting(enabled=True, delete=True)
        self.keywords = TelegramMessageCheckSetting(enabled=True, delete=False)


class TelegramMessageCheckSetting(EnabledFlag, DeleteFlag, AskFlag):
    def __init__(self, enabled=False, delete=False, ask=False):
        EnabledFlag.__init__(self, enabled)
        DeleteFlag.__init__(self, delete)
        AskFlag.__init__(self, ask)


def load_config(filename: str) -> Union[Config, tuple[Config, bool]]:
    config = Config()
    try:
        with open(filename, 'r') as file:
            data = yaml.safe_load(file)
            if data is None:
                return config, False

            paths_data = data.get('paths', {})
            config.paths.cache_dir = paths_data.get('cache_dir', config.paths.cache_dir)
            config.paths.scan_data_dir = paths_data.get('scan_data_dir', "scan-data")
            scan_data_suffixes_data = paths_data.get('scan_data_suffixes', {})
            config.paths.scan_data_suffixes.telegram_ids = scan_data_suffixes_data.get('telegram_ids', "tg-ids.txt")
            config.paths.scan_data_suffixes.telegram_user_names = scan_data_suffixes_data.get('telegram_user_names', "tg-user-names.txt")
            config.paths.scan_data_suffixes.telegram_usernames = scan_data_suffixes_data.get('telegram_usernames', "tg-usernames.txt")
            config.paths.scan_data_suffixes.telegram_keywords = scan_data_suffixes_data.get('telegram_keywords', "tg-keywords.txt")
            config.paths.scan_data_suffixes.telegram_urls = scan_data_suffixes_data.get('telegram_urls', "tg-urls.txt")
            config.paths.scan_data_suffixes.instagram_usernames = scan_data_suffixes_data.get('instagram_usernames', "ig-usernames.txt")
            config.paths.scan_data_suffixes.instagram_urls = scan_data_suffixes_data.get('instagram_urls', "ig-urls.txt")
            config.paths.scan_data_suffixes.instagram_names = scan_data_suffixes_data.get('instagram_names', "ig-names.txt")

            telegram_data = data.get('telegram', {})
            config.telegram.enabled = telegram_data.get('enabled', True)
            config.telegram.api_id = telegram_data.get('api_id', config.telegram.api_id)
            config.telegram.api_hash = telegram_data.get('api_hash', config.telegram.api_hash)
            config.telegram.from_date = telegram_data.get('from_date', None)
            if isinstance(config.telegram.from_date, str):
                config.telegram.from_date = datetime.strptime(config.telegram.from_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            config.telegram.to_date = telegram_data.get('to_date', None)
            if isinstance(config.telegram.to_date, str):
                config.telegram.to_date = datetime.strptime(config.telegram.to_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            config.telegram.cache_peers = telegram_data.get('cache_peers', False)
            config.telegram.cache_messages = telegram_data.get('cache_messages', False)

            dialogs_data = telegram_data.get('dialogs', {})
            config.telegram.dialogs.users.enabled = dialogs_data.get('users', {}).get('enabled', False)
            config.telegram.dialogs.users.ask = dialogs_data.get('users', {}).get('ask', False)
            config.telegram.dialogs.chats.enabled = dialogs_data.get('chats', {}).get('enabled', False)
            config.telegram.dialogs.chats.ask = dialogs_data.get('chats', {}).get('ask', False)
            config.telegram.dialogs.channels.enabled = dialogs_data.get('channels', {}).get('enabled', False)
            config.telegram.dialogs.channels.ask = dialogs_data.get('channels', {}).get('ask', False)
            config.telegram.dialogs.channels.self_only_after_users_count = dialogs_data.get('channels', {}).get('self_only_after_users_count', None)
            config.telegram.dialogs.channels.broadcast = dialogs_data.get('channels', {}).get('broadcast', False)
            config.telegram.dialogs.checks.enabled = dialogs_data.get('checks', {}).get('enabled', False)

            messages_data = telegram_data.get('messages', {})
            config.telegram.messages.enabled = messages_data.get('enabled', False)
            config.telegram.messages.delete = messages_data.get('delete', False)
            config.telegram.messages.ask = messages_data.get('ask', False)

            checks_data = messages_data.get('checks', {})
            config.telegram.messages.checks.urls.enabled = checks_data.get('urls', {}).get('enabled', False)
            config.telegram.messages.checks.urls.delete = checks_data.get('urls', {}).get('delete', False)
            config.telegram.messages.checks.urls.ask = checks_data.get('urls', {}).get('ask', False)
            config.telegram.messages.checks.forwards.enabled = checks_data.get('forwards', {}).get('enabled', False)
            config.telegram.messages.checks.forwards.delete = checks_data.get('forwards', {}).get('delete', False)
            config.telegram.messages.checks.forwards.ask = checks_data.get('forwards', {}).get('ask', False)
            config.telegram.messages.checks.keywords.enabled = checks_data.get('keywords', {}).get('enabled', False)
            config.telegram.messages.checks.keywords.delete = checks_data.get('keywords', {}).get('delete', False)
            config.telegram.messages.checks.keywords.ask = checks_data.get('keywords', {}).get('ask', False)

            instagram_data = data.get('instagram', {})
            config.instagram.enabled = instagram_data.get('enabled', True)
            config.instagram.data_dir = instagram_data.get('data_dir', "instagram-user-data")
            checks_data = instagram_data.get('checks', {})
            config.instagram.checks.reels_comments.enabled = checks_data.get('reels_comments', {}).get('enabled', True)
            config.instagram.checks.post_comments.enabled = checks_data.get('post_comments', {}).get('enabled', True)
            config.instagram.checks.comments_likes.enabled = checks_data.get('comments_likes', {}).get('enabled', True)
            config.instagram.checks.post_likes.enabled = checks_data.get('post_likes', {}).get('enabled', True)

    except FileNotFoundError:
        return config, False

    return config, True

if __name__ == "__main__":
    config = load_config("config.yaml")
    print(config)
