import re
import string
import os

import docx
from docx.document import Document
from docx.oxml import CT_Tbl, CT_P
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph

from scan_data import ScanDataEntry, ScanDataType
from cleanup.config.scan_config import load_config

def iterate_block_items(parent):
    if isinstance(parent, Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    else:
        raise ValueError("Something's not right")

    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)

def iterate_text(doc):
    for block in iterate_block_items(doc):
        if isinstance(block, Paragraph):
            yield block.text
        elif isinstance(block, Table):
            for row in block.rows:
                for cell in row.cells:
                    yield cell.text
                    for nested_block in iterate_block_items(cell):
                        if isinstance(nested_block, Paragraph):
                            yield nested_block.text
                        elif isinstance(nested_block, Table):
                            for nested_row in nested_block.rows:
                                for nested_cell in nested_row.cells:
                                    yield nested_cell.text

def filter_line(line):
    if line.startswith("Решение суда") or (line.startswith("от") or line.startswith("года.")) or line.startswith(
            'Подлежит немедленному исполнению') or not len(line.strip()):
        return False
    return True

def save_data_to_files(doc_name, mentions, config):
    base_name = os.path.splitext(doc_name)[0]
    scan_data_dir = config.paths.scan_data_dir
    suffixes = config.paths.scan_data_suffixes

    data_files = {
        ScanDataType.TG_USER_NAME: os.path.join(scan_data_dir, f"{base_name}-{suffixes.telegram_user_names}"),
        ScanDataType.TG_USERNAME: os.path.join(scan_data_dir, f"{base_name}-{suffixes.telegram_usernames}"),
        ScanDataType.TG_ID: os.path.join(scan_data_dir, f"{base_name}-{suffixes.telegram_ids}"),
        ScanDataType.TG_URL: os.path.join(scan_data_dir, f"{base_name}-{suffixes.telegram_urls}"),
        ScanDataType.INSTAGRAM_NAME: os.path.join(scan_data_dir, f"{base_name}-{suffixes.instagram_names}"),
        ScanDataType.INSTAGRAM_USERNAME: os.path.join(scan_data_dir, f"{base_name}-{suffixes.instagram_usernames}")
    }

    data_dict = {key: [] for key in data_files.keys()}

    for mention in mentions:
        data_dict[mention.data_type].append(mention.to_dict())

    for data_type, file_path in data_files.items():
        with open(file_path, 'w') as file:
            for data in data_dict[data_type]:
                file.write(f"{data['data']}\n")

def extract_telegram_mentions(doc_path, config):
    doc = docx.Document(doc_path)
    mentions = []
    processed_lines = set()

    for cell_text in iterate_text(doc):
        lines = cell_text.splitlines()
        for raw_line in filter(filter_line, lines):
            line = raw_line.strip()
            if line[-1] == '.':
                line = line[:-1]

            if line in processed_lines:
                continue
            processed_lines.add(line)
            new_mentions = process_line(line)
            if new_mentions:
                mentions.extend(new_mentions)

    save_data_to_files(os.path.basename(doc_path), mentions, config)
    print(f"Number of mentions found: {len(mentions)}")

def has_tg_mention(line):
    line_lower = line.lower()
    return ("@" in line_lower or
            "telegram" in line_lower or
            "телеграм" in line_lower or
            re.search(r't\.me/([a-zA-Z0-9._]+)', line_lower) or
            re.search(r'ID.*?(\d+)', line_lower))

common_mentions = ["telegram", "facebook", "instagram", "вконтакте", "vk", "twitter", "youtube", "joinchat",
                   "одноклассники", "tiktok", 'tik-tok', 'Tik-Ток', "addstikers", "addstickers",
                   "belarus"]

def extract_urls(line: string):
    if not "интернет-сайт" in line.lower():
        return []
    url_pattern = re.compile(
        r'(((http|https)://)?[a-zA-Z0-9./?:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9.&/?:@\-_=#])*)')
    found_urls = list(filter(filter_mentions(common_mentions), map(lambda x: x[0], url_pattern.findall(line))))
    found_urls = list(map(clear_url, found_urls))
    return list(map(lambda x: ScanDataEntry(
        data=x,
        data_type=ScanDataType.TG_URL
    ), found_urls))

def clear_url(line):
    line = re.sub(r'((http|https)://)?', '', line)
    return re.sub(r'www.', '', line)

def filter_mentions(mentions):
    def filter_mention(line):
        for m in mentions:
            if m in line:
                return False
        return True

    return filter_mention

def extract_tg_names(line):
    if not has_tg_mention(line):
        return []
    chat_name_pattern = re.compile(r'"(.*?)"')
    return map(lambda x: ScanDataEntry(
        data=x,
        data_type=ScanDataType.TG_USER_NAME
    ), list(chat_name_pattern.findall(line)))

def extract_tg_usernames(line):
    if not has_tg_mention(line):
        return []
    username_pattern = re.compile(r't\.me/([a-zA-Z0-9._]+)')
    username_pattern2 = re.findall(r'@([a-zA-Z0-9._]+)', line)
    return list(map(lambda x: ScanDataEntry(
        data=x,
        data_type=ScanDataType.TG_USERNAME
    ), list(filter(lambda x: len(x) > 2, username_pattern.findall(line) + username_pattern2))))

def extract_tg_ids(line):
    if not has_tg_mention(line):
        return []
    id_pattern = re.compile(r'ID.*?(\d+)')
    return list(map(lambda x: ScanDataEntry(
        data=x,
        data_type=ScanDataType.TG_ID
    ), list(id_pattern.findall(line))))

def has_instagram_mention(line):
    return "instagram" in line.lower() or "инстаграм" in line.lower() or re.search(r'instagram.com/([a-zA-Z0-9._]+)',
                                                                                   line)

def extract_instagram_names(line):
    if not has_instagram_mention(line):
        return []
    chat_name_pattern = re.compile(r'"(.*?)"')
    return list(map(lambda x: ScanDataEntry(
        data=x,
        data_type=ScanDataType.INSTAGRAM_NAME
    ), list(chat_name_pattern.findall(line))))

def extract_instagram_usernames(line):
    if not has_instagram_mention(line):
        return []
    username_pattern = re.compile(r'instagram.com/([a-zA-Z0-9._]+)')
    username_pattern2 = re.findall(r'@([a-zA-Z0-9._]+)', line)
    return list(map(lambda x: ScanDataEntry(
        data=x,
        data_type=ScanDataType.INSTAGRAM_USERNAME
    ), list(username_pattern.findall(line)) + username_pattern2))

def process_line(line):
    found = []
    found.extend(extract_tg_names(line))
    found.extend(extract_tg_usernames(line))
    found.extend(extract_tg_ids(line))

    found.extend(extract_instagram_names(line))
    found.extend(extract_instagram_usernames(line))
    found.extend(extract_urls(line))

    found = filter(
        lambda x: len(x.data) > 3 and
                  x.data.lower() not in ["", "telegram", "facebook", "instagram", "вконтакте",
                                         "vk", "twitter",
                                         "youtube", "joinchat", "одноклассники", "tiktok",
                                         'tik-tok', 'Tik-Ток', "addstikers", "addstickers",
                                         "lida", "user", "belarus", "youtube.com", "anya", "новы", "суд",
                                         "alexander", "most", "explore", "gmail.com", "tik tok", "ivan",
                                         "настоящее время", "artem"],
        found)

    return found

if __name__ == "__main__":
    config, _ = load_config("config.yaml")
    extract_telegram_mentions('extreme-by.docx', config)
    # save_doc_to_plain("extreme-by.docx", 'cache/unwanted.txt')
