"""Tests for providers/base.py — system_prompt, _build_prompt, _parse_sections."""

import unittest
from unittest.mock import patch

# Load English translations so t() works
from core.i18n import load as i18n_load
i18n_load("en")

from providers.base import system_prompt, AIProvider


class _TestableProvider(AIProvider):
    """Concrete subclass of AIProvider for testing non-abstract methods."""
    def analyze(self, event: dict) -> dict:
        return {}

    def validate_api_key(self, api_key: str) -> bool:
        return True


class TestSystemPrompt(unittest.TestCase):
    """Tests for the system_prompt() function."""

    def test_returns_string(self):
        """system_prompt() should return a non-empty string."""
        prompt = system_prompt()
        self.assertIsInstance(prompt, str)
        self.assertTrue(len(prompt) > 0)

    def test_contains_section_markers(self):
        """Should contain all four emoji section markers."""
        prompt = system_prompt()
        for emoji in ["🔍", "⚠️", "🔧", "💡"]:
            self.assertIn(emoji, prompt)

    def test_contains_english_label(self):
        """With English locale, the prompt should reference English section names."""
        prompt = system_prompt()
        self.assertIn("what is this", prompt.lower())

    @patch("providers.base.t")
    def test_uses_current_language(self, mock_t):
        """Should use the current language from t()."""
        mock_t.side_effect = lambda key, **kw: {
            "_language_name": "Polski",
            "section_what_is": "Co to jest",
            "section_is_serious": "Czy to poważne",
            "section_what_to_do": "Co zrobić",
            "section_tip": "Wskazówka",
        }.get(key, key)

        prompt = system_prompt()
        self.assertIn("polski", prompt.lower())
        self.assertIn("co to jest", prompt.lower())


class TestBuildPrompt(unittest.TestCase):
    """Tests for AIProvider._build_prompt()."""

    def setUp(self):
        self.provider = _TestableProvider()

    def test_builds_string_from_event(self):
        """Should produce a non-empty string from a valid event dict."""
        event = {
            "SourceName": "TestSource",
            "EventID": 1234,
            "Level": "Error",
            "TimeGenerated": "2026-06-24 12:00:00",
            "Message": "Something went wrong.",
        }
        prompt = self.provider._build_prompt(event)
        self.assertIsInstance(prompt, str)
        self.assertIn("TestSource", prompt)
        self.assertIn("1234", prompt)

    def test_handles_partial_event(self):
        """Should survive missing keys without crashing."""
        event = {}
        prompt = self.provider._build_prompt(event)
        self.assertIsInstance(prompt, str)


class TestParseSections(unittest.TestCase):
    """Tests for AIProvider._parse_sections()."""

    def test_parses_all_four_sections(self):
        """A response with all four emoji sections should be fully parsed."""
        text = (
            "🔍 What is this: A test event\n"
            "⚠️ Is it serious: Not really\n"
            "🔧 What to do: Restart the service\n"
            "💡 Tip: Check the logs first\n"
        )
        result = AIProvider._parse_sections(text)
        self.assertEqual(result["explanation"], "A test event")
        self.assertEqual(result["severity"], "Not really")
        self.assertEqual(result["steps"], "Restart the service")
        self.assertEqual(result["tip"], "Check the logs first")

    def test_multiline_content(self):
        """Section content spanning multiple lines should be joined."""
        text = (
            "🔍 What is this:\n"
            "First line\n"
            "Second line\n"
            "⚠️ Is it serious: Yes\n"
        )
        result = AIProvider._parse_sections(text)
        self.assertIn("First line", result["explanation"])
        self.assertIn("Second line", result["explanation"])
        self.assertEqual(result["severity"], "Yes")

    def test_missing_sections_default_to_empty(self):
        """Sections not present in the text should default to empty string."""
        text = "🔍 Only an explanation here\n"
        result = AIProvider._parse_sections(text)
        self.assertEqual(result["explanation"], "Only an explanation here")
        self.assertEqual(result["severity"], "")
        self.assertEqual(result["steps"], "")
        self.assertEqual(result["tip"], "")

    def test_empty_string(self):
        """An empty string should produce empty sections."""
        result = AIProvider._parse_sections("")
        self.assertEqual(result["explanation"], "")
        self.assertEqual(result["severity"], "")
        self.assertEqual(result["steps"], "")
        self.assertEqual(result["tip"], "")

    def test_no_emoji_markers(self):
        """Text without emoji markers should produce empty sections."""
        text = "Just some plain text with no emoji markers.\nSecond line."
        result = AIProvider._parse_sections(text)
        self.assertEqual(result["explanation"], "")
        self.assertEqual(result["severity"], "")
        self.assertEqual(result["steps"], "")
        self.assertEqual(result["tip"], "")

    def test_dots_placeholder_skipped(self):
        """Section with '...' as content should be treated as empty."""
        text = "🔍 What is this: ...\n⚠️ Is it serious: Real content\n"
        result = AIProvider._parse_sections(text)
        self.assertEqual(result["explanation"], "")
        self.assertEqual(result["severity"], "Real content")

    def test_emoji_without_label(self):
        """Section starting with just an emoji (no label text) should still parse."""
        text = "🔍 Just the content\n"
        result = AIProvider._parse_sections(text)
        self.assertEqual(result["explanation"], "Just the content")

    def test_content_with_colons(self):
        """Content containing colons should not be truncated."""
        text = "💡 Tip: Check: the: logs\n"
        result = AIProvider._parse_sections(text)
        self.assertEqual(result["tip"], "Check: the: logs")

    def test_leading_trailing_whitespace(self):
        """Whitespace around section content should be stripped."""
        text = "🔍   Spacy content   \n"
        result = AIProvider._parse_sections(text)
        self.assertEqual(result["explanation"], "Spacy content")


if __name__ == "__main__":
    unittest.main()
