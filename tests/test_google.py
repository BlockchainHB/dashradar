import pytest
import re
from bot.google import DOORDASH_PATTERN, UBEREATS_PATTERN, SKIP_PATTERN


class TestRegexPatterns:
    def test_doordash_pattern_matches(self):
        html = '''<a href="https://www.doordash.com/store/test-restaurant-toronto-12345">Order</a>'''
        matches = DOORDASH_PATTERN.findall(html)
        assert len(matches) == 1
        assert "doordash.com/store/" in matches[0]

    def test_doordash_pattern_without_www(self):
        html = '''<a href="https://doordash.com/store/test-12345">Order</a>'''
        matches = DOORDASH_PATTERN.findall(html)
        assert len(matches) == 1

    def test_ubereats_pattern_matches(self):
        html = '''<a href="https://www.ubereats.com/store/test-restaurant">Order</a>'''
        matches = UBEREATS_PATTERN.findall(html)
        assert len(matches) == 1
        assert "ubereats.com/" in matches[0]

    def test_skip_pattern_matches(self):
        html = '''<a href="https://www.skipthedishes.com/test-restaurant">Order</a>'''
        matches = SKIP_PATTERN.findall(html)
        assert len(matches) == 1
        assert "skipthedishes.com/" in matches[0]

    def test_no_match_for_unrelated_url(self):
        html = '''<a href="https://www.google.com/search">Search</a>'''
        assert len(DOORDASH_PATTERN.findall(html)) == 0
        assert len(UBEREATS_PATTERN.findall(html)) == 0
        assert len(SKIP_PATTERN.findall(html)) == 0
