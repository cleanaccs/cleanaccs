import json
import re
import string

import docx
from docx.document import Document
from docx.oxml import CT_Tbl, CT_P
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph

from channel import UnwantedMaterial, MaterialType


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
            # Process text in paragraphs
            yield block.text
        elif isinstance(block, Table):
            # Process text in table cells
            for row in block.rows:
                for cell in row.cells:
                    yield cell.text
                    # Recursively process text in nested tables
                    for nested_block in iterate_block_items(cell):
                        if isinstance(nested_block, Paragraph):
                            yield nested_block.text
                        elif isinstance(nested_block, Table):
                            for nested_row in nested_block.rows:
                                for nested_cell in nested_row.cells:
                                    yield nested_cell.text


def save_doc_to_plain(doc_path, output_file):
    # Load the document
    doc = docx.Document(doc_path)

    lines = set()
    with open(output_file, 'w') as file:
        for text in filter(filter_line, iterate_text(doc)):
            if text not in lines:
                file.write(text + "\n")
                lines.add(text)


def filter_line(line):
    if line.startswith("Решение суда") or (line.startswith("от") or line.startswith("года.")) or line.startswith(
            'Подлежит немедленному исполнению') or not len(line.strip()):
        return False
    return True


# Function to extract Telegram mentions from a .docx file
def extract_telegram_mentions(doc_path, output_file):
    # Load the document
    doc = docx.Document(doc_path)

    # Regex patterns to identify Telegram cells and extract data
    telegram_cell_pattern = re.compile(r'(telegram|телеграм|t\.me)', re.IGNORECASE)

    mentions = []
    processed_lines = set()

    for cell_text in iterate_text(doc):
        # Check if the cell contains Telegram-related information
        # Split the cell text into lines and treat each line separately
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

    mentions.append(UnwantedMaterial("ВЯЧОРКА", MaterialType.TG_NAME))
    mentions.append(UnwantedMaterial("viacorka", MaterialType.TG_USERNAME))
    mentions.append(UnwantedMaterial("HotLine", MaterialType.TG_NAME))
    mentions.append(UnwantedMaterial("help_bysol", MaterialType.TG_USERNAME))
    mentions.append(UnwantedMaterial("BySol Evacuation", MaterialType.TG_NAME))
    mentions.append(UnwantedMaterial("bysol_evacuation", MaterialType.TG_USERNAME))
    mentions.append(UnwantedMaterial("BySol Evacuation", MaterialType.TG_NAME))
    mentions.append(UnwantedMaterial("BelarusKrakow", MaterialType.TG_USERNAME))
    mentions.append(UnwantedMaterial("Onliner", MaterialType.TG_NAME))
    mentions.append(UnwantedMaterial("onlinerby", MaterialType.TG_USERNAME))
    mentions.append(UnwantedMaterial("Раньше всех. Ну почти", MaterialType.TG_NAME))
    mentions.append(UnwantedMaterial("bbbreaking", MaterialType.TG_USERNAME))
    mentions.append(UnwantedMaterial("Беларусь Сегодня", MaterialType.TG_NAME))
    mentions.append(UnwantedMaterial("belarus_news_onlinerby", MaterialType.TG_USERNAME))
    mentions.append(UnwantedMaterial("Telegram Беларусь", MaterialType.TG_NAME))
    mentions.append(UnwantedMaterial("telegrambelarus", MaterialType.TG_USERNAME))
    mentions.append(UnwantedMaterial("Беларусь 2020", MaterialType.TG_NAME))
    mentions.append(UnwantedMaterial("belarus2020", MaterialType.TG_USERNAME))
    mentions.append(UnwantedMaterial("Грушвилль", MaterialType.TG_NAME))
    mentions.append(UnwantedMaterial("grushville", MaterialType.TG_USERNAME))
    mentions.append(UnwantedMaterial("Советская Белоруссия", MaterialType.TG_NAME))
    mentions.append(UnwantedMaterial("sovbelorussia", MaterialType.TG_USERNAME))
    mentions.append(UnwantedMaterial("golosby_bot", MaterialType.TG_USERNAME))
    mentions.append(UnwantedMaterial("zabynet", MaterialType.TG_USERNAME))
    mentions.append(UnwantedMaterial("Не БТ", MaterialType.TG_NAME))
    mentions.append(UnwantedMaterial("Perepichka", MaterialType.TG_NAME))
    # mentions.append(UnwantedMaterial("dvachannel", MaterialType.TG_USERNAME))
    mentions.append(UnwantedMaterial("Трыкатаж", MaterialType.TG_NAME))
    mentions.append(UnwantedMaterial("spitzfirst", MaterialType.TG_USERNAME))
    mentions.append(UnwantedMaterial("chilikto", MaterialType.TG_USERNAME))
    mentions.append(UnwantedMaterial("dzik_pic", MaterialType.TG_USERNAME))
    mentions.append(UnwantedMaterial("radiosvoboda", MaterialType.TG_USERNAME))
    mentions.append(UnwantedMaterial("radiosvaboda", MaterialType.TG_USERNAME))
    mentions.append(UnwantedMaterial("svoboda_radio", MaterialType.TG_USERNAME))
    mentions.append(UnwantedMaterial("inter.minsk", MaterialType.TG_USERNAME))
    mentions.append(UnwantedMaterial("voicesfrombelarus", MaterialType.TG_USERNAME))
    mentions.append(UnwantedMaterial("devby", MaterialType.TG_USERNAME))
    mentions.append(UnwantedMaterial("jerasevic", MaterialType.TG_USERNAME))
    mentions.append(UnwantedMaterial("belarus22", MaterialType.TG_USERNAME))
    mentions.append(UnwantedMaterial("crimebelarus", MaterialType.TG_USERNAME))
    mentions.append(UnwantedMaterial("CyberPartisan", MaterialType.TG_USERNAME))
    mentions.append(UnwantedMaterial("talernews", MaterialType.TG_USERNAME))
    mentions.append(UnwantedMaterial("BGMnews_bot", MaterialType.TG_USERNAME))

    mentions.append(UnwantedMaterial("pkritchko", MaterialType.INSTAGRAM_LINK))
    mentions.append(UnwantedMaterial("prezident.sveta", MaterialType.INSTAGRAM_LINK))
    mentions.append(UnwantedMaterial("dzik_pic", MaterialType.INSTAGRAM_LINK))
    mentions.append(UnwantedMaterial("bypolofficial", MaterialType.INSTAGRAM_LINK))
    mentions.append(UnwantedMaterial("bysolfund", MaterialType.INSTAGRAM_LINK))
    mentions.append(UnwantedMaterial("bysolfund", MaterialType.INSTAGRAM_LINK))
    mentions.append(UnwantedMaterial("inter.minsk", MaterialType.INSTAGRAM_LINK))
    mentions.append(UnwantedMaterial("liliya_akhremchyk", MaterialType.INSTAGRAM_LINK))
    mentions.append(UnwantedMaterial("mc_maxim", MaterialType.INSTAGRAM_LINK))
    mentions.append(UnwantedMaterial("pkritchko", MaterialType.INSTAGRAM_LINK))
    mentions.append(UnwantedMaterial("jerasevic", MaterialType.INSTAGRAM_LINK))
    mentions.append(UnwantedMaterial("lineysfilm", MaterialType.INSTAGRAM_LINK))
    mentions.append(UnwantedMaterial("toxaby", MaterialType.INSTAGRAM_LINK))

    mentions.append(UnwantedMaterial("https://bit.ly/obraschenie2020", MaterialType.URL))
    mentions.append(UnwantedMaterial("naviny.by", MaterialType.URL))
    mentions.append(UnwantedMaterial('blacklist2020.netlify.app', MaterialType.URL))
    # mentions.append(UnwantedMaterial('dev.by', MaterialType.URL))
    mentions.append(UnwantedMaterial('tut.by', MaterialType.URL))
    mentions.append(UnwantedMaterial('naviny.by', MaterialType.URL))
    # mentions.append(UnwantedMaterial('onliner.by', MaterialType.URL))

    mentions.append(UnwantedMaterial("призыву нет", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Трыкатаж", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("коронавирус", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("навальный", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("honestpeople", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("тихановская", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("бабарико", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("nexta", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("zerkalo", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("zerkaloio", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("ебларусь", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("донаты", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("донатил", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("tutby", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("шпиц первого", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("прокопьев", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("ермошина", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("фальсификации", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("фальсификация", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("mikitamikado", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("выбарчая", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("саня уходи", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("задержанных", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("протестующих", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Протасевич", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("президент беларуси", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Perepichka", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("максим знак", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("кулуары куку", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Выборы в Беларуси", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("9 августа", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("жыве", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Марш свободы", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Марш единства", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Женский марш", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Марш пенсионеров", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Забастовки", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Координационный", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("ОМОН", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Задержания", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("пытки", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Политзаключенные", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Политзаключенный", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Площадь перемен", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Бондаренко", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("бчб", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Погоня", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Пагоня", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("nexta", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("нехта", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Уходи!", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Саша 3%", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("3%", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("97%", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("усатый", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("pasaran", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Цепкало", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Колесникова", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Калесникова", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Латушко", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Страна для жизни", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Честные люди", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Молодой фронт", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Европейская Беларусь", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("верым", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("можам", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("пераможам", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("перамога", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("КГК", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("БЧБ", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("🤍❤️🤍", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("губоп", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("кгб", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("гэбня", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Лугабе", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("лукаш", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("стычки", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("плошчу", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("беркут", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Imaguru", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("имагуру", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Радыё Свабода", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("уголовка", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("административка", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("тюрьма", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("окрестина", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("жодино", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("повестка", MaterialType.TG_KEYWORD))
    # mentions.append(UnwantedMaterial("суд", MaterialType.MENTION))
    mentions.append(UnwantedMaterial("выборы", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("марш", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Каратели Беларуси", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Белсат", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("BELSAT", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("хартия", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("Хартыя", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("лосик", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("ВЯСНА", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("мотолько", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("диктатор", MaterialType.TG_KEYWORD))
    mentions.append(UnwantedMaterial("диктатура", MaterialType.TG_KEYWORD))

    # mentions.append(UnwantedMaterial("лукашенко", MaterialType.MENTION))
    # mentions.append(UnwantedMaterial("путин", MaterialType.MENTION))

    # Write the results to the output file in JSON format
    with open(output_file, 'w') as file:
        json.dump([chat.to_dict() for chat in mentions], file, ensure_ascii=False, indent=2)

    # Print the number of mentions found
    print(f"Number of mentions found: {len(mentions)}")


def has_tg_mention(line):
    line_lower = line.lower()
    return ("@" in line_lower or
            "telegram" in line_lower or
            "телеграм" in line_lower or
            re.search(r't\.me/([a-zA-Z0-9._]+)', line_lower) or
            re.search(r'ID.*?(\d+)', line_lower))
    # re.search(r'@(\w+)', line)


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
    return list(map(lambda x: UnwantedMaterial(
        material=x,
        source=MaterialType.URL
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
    return map(lambda x: UnwantedMaterial(
        material=x,
        source=MaterialType.TG_NAME
    ), list(chat_name_pattern.findall(line)))


def extract_tg_usernames(line):
    if not has_tg_mention(line):
        return []
    username_pattern = re.compile(r't\.me/([a-zA-Z0-9._]+)')
    username_pattern2 = re.findall(r'@([a-zA-Z0-9._]+)', line)
    return list(map(lambda x: UnwantedMaterial(
        material=x,
        source=MaterialType.TG_USERNAME
    ), list(filter(lambda x: len(x) > 2, username_pattern.findall(line) + username_pattern2))))


def extract_tg_ids(line):
    if not has_tg_mention(line):
        return []
    id_pattern = re.compile(r'ID.*?(\d+)')
    return list(map(lambda x: UnwantedMaterial(
        material=x,
        source=MaterialType.TG_ID
    ), list(id_pattern.findall(line))))


def has_instagram_mention(line):
    return "instagram" in line.lower() or "инстаграм" in line.lower() or re.search(r'instagram.com/([a-zA-Z0-9._]+)',
                                                                                   line)


def extract_instagram_names(line):
    if not has_instagram_mention(line):
        return []
    chat_name_pattern = re.compile(r'"(.*?)"')
    return list(map(lambda x: UnwantedMaterial(
        material=x,
        source=MaterialType.INSTAGRAM_NAME
    ), list(chat_name_pattern.findall(line))))


def extract_instagram_urls(line):
    if not has_instagram_mention(line):
        return []
    username_pattern = re.compile(r'instagram.com/([a-zA-Z0-9._]+)')
    username_pattern2 = re.findall(r'@([a-zA-Z0-9._]+)', line)
    return list(map(lambda x: UnwantedMaterial(
        material=x,
        source=MaterialType.INSTAGRAM_LINK
    ), list(username_pattern.findall(line)) + username_pattern2))


def process_line(line):
    found = []
    found.extend(extract_tg_names(line))
    found.extend(extract_tg_usernames(line))
    found.extend(extract_tg_ids(line))

    found.extend(extract_instagram_names(line))
    found.extend(extract_instagram_urls(line))
    found.extend(extract_urls(line))

    found = filter(
        lambda x: len(x.material) > 3 and
                  x.material.lower() not in ["", "telegram", "facebook", "instagram", "вконтакте",
                                             "vk", "twitter",
                                             "youtube", "joinchat", "одноклассники", "tiktok",
                                             'tik-tok', 'Tik-Ток', "addstikers", "addstickers",
                                             "lida", "user", "belarus", "youtube.com", "anya", "новы", "суд",
                                             "alexander", "most", "explore", "gmail.com", "tik tok", "ivan",
                                             "настоящее время"],
        found)

    return found


if __name__ == "__main__":
    # Run the extraction
    # test_line = "Аккаунт \"belarusla\" социальной сети \"Instagram\", имеющий идентификатор https://www.instagram.com/belarusla?igshid=NDk5N2NIZjQ=."
    # print(has_instagram_mention(test_line))

    extract_telegram_mentions('ex.docx', 'cache/unwanted_2.json')
    # print(list(map(lambda x: x.to_str(), extract_instagram_urls(
    #     )
    # )))
    save_doc_to_plain("ex.docx", 'cache/unwanted.txt')

# hardwomenbelarus
