from tg_bot.static.emojis import Emoji


def replace_emojis(text: str) -> str:
    for emoji in Emoji:
        text = text.replace(str(emoji), '')
    return text


def cleanup(text) -> str:
    return replace_emojis(text).strip()
