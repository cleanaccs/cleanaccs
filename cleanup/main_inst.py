import json
import os
import string
from datetime import datetime

from cleanup.docextract.channel import ScanDataType
from docextract.channel import load_unwanted_materials

# Set cache directory
cache_dir = 'cache'
os.makedirs(cache_dir, exist_ok=True)

def load_json_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print("Error: File not found.")
        return None
    except json.JSONDecodeError:
        print("Error: Could not decode JSON.")
        return None

def get_field_value(entry, field_path: string, default=None):
    fields = field_path.split('.')
    value = entry
    for field in fields:
        value = value.get(field, {})
        if not value:
            return default
    return value

def check_reels_comments(folder_name, inst_accounts):
    print("Checking reels comments...")
    json_data = load_json_file(folder_name + "/your_instagram_activity/comments/reels_comments.json")
    if "comments_reels_comments" in json_data:
        for comment in json_data["comments_reels_comments"]:
            media_owner_value = get_field_value(comment, "string_map_data.Media Owner.value")

            if media_owner_value in inst_accounts:
                timestamp = get_field_value(comment, "string_map_data.Time.timestamp")
                if timestamp:
                    timestamp_iso = datetime.fromtimestamp(timestamp).isoformat()
                    print(f"Media Owner '{media_owner_value}' is in the list of specific values. Timestamp: {timestamp_iso}")


def check_post_comments(folder_name, inst_accounts):
    print("Checking post comments...")
    json_data = load_json_file(folder_name + "/your_instagram_activity/comments/post_comments_1.json")
    # Iterate over all comments and check Media Owner for the new JSON format
    for entry in json_data:
        if "string_map_data" in entry:
            media_owner_data = entry["string_map_data"].get("Media Owner", {})
            media_owner_value = media_owner_data.get("value", "")

            if media_owner_value in inst_accounts:
                timestamp = entry["string_map_data"].get("Time", {}).get("timestamp", None)
                if timestamp:
                    timestamp_iso = datetime.fromtimestamp(timestamp).isoformat()
                    print(f"Media Owner '{media_owner_value}' is in the list of specific values. Timestamp: {timestamp_iso}")


def check_liked_comments(folder_name, inst_accounts):
    print("Checking likes under comments...")
    json_data = load_json_file(folder_name + "/your_instagram_activity/likes/liked_comments.json")
    if "likes_comment_likes" in json_data:
        for like in json_data["likes_comment_likes"]:
            title = like.get("title", "")
            if title in inst_accounts:
                for data in like.get("string_list_data", []):
                    timestamp = data.get("timestamp", None)
                    if timestamp:
                        timestamp_iso = datetime.fromtimestamp(timestamp).isoformat()
                        print(f"Title '{title}' is in the list of specific values. Timestamp: {timestamp_iso}")


def check_liked_posts(folder_name, inst_accounts):
    print("Checking likes under posts...")
    json_data = load_json_file(folder_name + "/your_instagram_activity/likes/liked_posts.json")
    if "likes_media_likes" in json_data:
        for like in json_data["likes_media_likes"]:
            title = like.get("title", "")
            if title in inst_accounts:
                for data in like.get("string_list_data", []):
                    timestamp = data.get("timestamp", None)
                    if timestamp:
                        timestamp_iso = datetime.fromtimestamp(timestamp).isoformat()
                        print(f"Title '{title}' is in the list of specific values. Timestamp: {timestamp_iso}")

def iterate_over_inbox_json_files(root_dir, inst_accounts):
    inbox_path = os.path.join(root_dir, 'your_instagram_activity', 'messages', 'inbox')
    if not os.path.exists(inbox_path):
        print(f"Error: Inbox path not found at {inbox_path}.")
        return

    for folder_name in os.listdir(inbox_path):
        folder_path = os.path.join(inbox_path, folder_name)
        if os.path.isdir(folder_path):
            for file_name in os.listdir(folder_path):
                if file_name.endswith('.json'):
                    # print(f"Processing file {file_name}...")
                    file_path = os.path.join(folder_path, file_name)
                    json_data = load_json_file(file_path)
                    if json_data:
                        if "messages" in json_data:
                            for entry in json_data.get("messages", []):
                                content_owner = get_field_value(entry, "share.original_content_owner")
                                if content_owner and content_owner in inst_accounts:
                                    timestamp = get_field_value(entry, "timestamp_ms")
                                    if timestamp:
                                        timestamp_iso = datetime.fromtimestamp(timestamp / 1000).isoformat()
                                        print(f"'{content_owner}'. ${folder_name}. Timestamp: {timestamp_iso}")

def check_followers(folder_name, inst_accounts):
    print("Checking followers...")
    json_data = load_json_file(folder_name + "/connections/followers_and_following/followers_1.json")

    for follower in json_data:
        l = follower.get("string_list_data", [])
        for title in l:
            value = title.get("value", "")
            if value in inst_accounts:
                print(f"Follower '{value}' is in the list of specific values. ")

def check_following(folder_name, inst_accounts):
    print("Checking following...")
    json_data = load_json_file(folder_name + "/connections/followers_and_following/following.json")

    for follower in json_data.get("relationships_following", []):
        l = follower.get("string_list_data", [])
        for title in l:
            value = title.get("value", "")
            if value in inst_accounts:
                print(f"Follower '{value}' is in the list of specific values. ")

def check_instagram(folder_name):
    unwanted = load_unwanted_materials(os.path.join(cache_dir, "unwanted_2.json"))
    inst_usernames = [item.data for item in unwanted if (item.data_type.to_str() == ScanDataType.INSTAGRAM_USERNAME.to_str() or item.data_type.to_str() == ScanDataType.INSTAGRAM_NAME.to_str())]
    check_reels_comments(folder_name, inst_usernames)
    check_post_comments(folder_name, inst_usernames)

    check_liked_comments(folder_name, inst_usernames)
    check_liked_posts(folder_name, inst_usernames)
    iterate_over_inbox_json_files(folder_name, inst_usernames)
    check_followers(folder_name, inst_usernames)
    check_following(folder_name, inst_usernames)

if __name__ == "__main__":
    check_instagram("instagram/instagram-archive")
