import json
import os

from telethon.tl.types import User, Channel, Chat


class CachedUser:
    def __init__(self, chat):
        self.id = chat.id
        self.username = getattr(chat, 'username', 'unknown')
        self.title = getattr(chat, 'title', 'unknown') or getattr(chat, 'name', 'unknown')
        self.is_user = isinstance(chat, User)
        self.is_chat = isinstance(chat, Chat)
        self.is_channel = isinstance(chat, Channel)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'title': self.title,
            'is_user': self.is_user,
            'is_chat': self.is_chat,
            'is_channel': self.is_channel,
        }

    @classmethod
    def from_dict(cls, data):
        instance = cls.__new__(cls)
        instance.id = data['id']
        instance.username = data['username']
        instance.title = data['title']
        instance.is_user = data['is_user']
        instance.is_chat = data['is_chat']
        instance.is_channel = data['is_channel']
        return instance


class ChatCache:
    def __init__(self, cache_file, client):
        self.cache_file = cache_file
        self.client = client
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                self.chat_cache = {key: CachedUser.from_dict(value) for key, value in json.load(f).items()}
        else:
            self.chat_cache = {}

    def save_chat_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump({key: value.to_dict() for key, value in self.chat_cache.items()}, f)

    async def get_chat_entity(self, peer_id):
        peer_id_str = str(peer_id)
        if peer_id_str in self.chat_cache:
            return self.chat_cache[peer_id_str]
        else:
            chat = await self.client.get_entity(peer_id)
            cached_user = CachedUser(chat)
            self.chat_cache[peer_id_str] = cached_user
            self.save_chat_cache()
            return cached_user


class CachedProcessedUser:
    def __init__(self, id, version, username, name, count, deleted_count):
        self.id = id
        self.version = version
        self.username = username
        self.name = name
        self.count = count
        self.deleted_count = deleted_count

    def to_dict(self):
        return {
            'id': self.id,
            'version': self.version,
            'username': self.username,
            'name': self.name,
            'count': self.count,
            'deleted_count': self.deleted_count,
        }

    def __dict__(self):
        return self.to_dict()

    @classmethod
    def from_dict(cls, data):
        instance = cls.__new__(cls)
        instance.id = data['id']
        instance.version = data['version']
        instance.username = data['username']
        instance.name = data['name']
        instance.count = data['count']
        instance.deleted_count = data['deleted_count']
        return instance


class ProcessedUsersCache:
    def __init__(self, cache_file):
        self.cache_file = cache_file
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                self.processed_users_cache = {key: CachedProcessedUser.from_dict(value) for key, value in
                                              json.load(f).items()}
        else:
            self.processed_users_cache = {}

    def save_processed_users_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump({key: value.to_dict() for key, value in self.processed_users_cache.items()}, f)

    def get_processed_user_version(self, user_id):
        user_id_str = str(user_id)
        if user_id_str in self.processed_users_cache:
            return self.processed_users_cache[user_id_str].version
        else:
            return 0

    def is_processed(self, user_id, version):
        return self.get_processed_user_version(user_id) == version

    def update_processed(self, user_id, version, username, name, total_count, deleted_count):
        user_id_str = str(user_id)
        self.processed_users_cache[user_id_str] = CachedProcessedUser(user_id, version, username, name, total_count,
                                                                      deleted_count)
        self.save_processed_users_cache()

    def clear_cache(self):
        self.processed_users_cache = {}
        self.save_processed_users_cache()
