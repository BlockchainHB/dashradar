def is_valid_address(text: str) -> bool:
    """Basic validation that text looks like an address."""
    if len(text) < 10:
        return False
    if not any(c.isdigit() for c in text):
        return False
    return True


def escape_markdown_v2(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    # Backslash must be escaped FIRST to avoid double-escaping
    text = text.replace('\\', '\\\\')
    # All other special characters that need escaping in MarkdownV2
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text


# Keep old name for backwards compatibility
def escape_markdown(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    return escape_markdown_v2(text)
