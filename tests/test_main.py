import pytest
from bot.utils import is_valid_address, escape_markdown


class TestAddressValidation:
    def test_valid_address(self):
        assert is_valid_address("123 Queen St W, Toronto, ON") is True
        assert is_valid_address("456 Main Street, Vancouver") is True
        assert is_valid_address("789 Broadway Ave, New York, NY 10001") is True

    def test_invalid_address_too_short(self):
        assert is_valid_address("123 Main") is False
        assert is_valid_address("short") is False

    def test_invalid_address_no_numbers(self):
        assert is_valid_address("Queen Street West, Toronto") is False
        assert is_valid_address("no numbers here at all") is False


class TestEscapeMarkdown:
    def test_escape_asterisk(self):
        assert escape_markdown("*bold*") == "\\*bold\\*"

    def test_escape_underscore(self):
        assert escape_markdown("_italic_") == "\\_italic\\_"

    def test_escape_brackets(self):
        assert escape_markdown("[link](url)") == "\\[link\\]\\(url\\)"

    def test_no_escape_needed(self):
        assert escape_markdown("plain text") == "plain text"

    def test_mixed_special_chars(self):
        result = escape_markdown("Test *Restaurant* - #1")
        assert "\\*" in result
        assert "\\#" in result
        assert "\\-" in result
