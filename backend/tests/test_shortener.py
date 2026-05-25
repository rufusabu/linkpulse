"""
Unit tests for app.shortener.generate_code.

These tests are synchronous — generate_code has no I/O — so no async fixtures
are needed here.
"""

import string

from app.shortener import generate_code

_BASE62 = string.ascii_letters + string.digits  # a-zA-Z0-9


class TestGenerateCodeLength:
    def test_default_length_is_7(self):
        """generate_code() with no arguments produces exactly 7 characters."""
        assert len(generate_code()) == 7

    def test_custom_length_1(self):
        assert len(generate_code(length=1)) == 1

    def test_custom_length_12(self):
        assert len(generate_code(length=12)) == 12

    def test_custom_length_0(self):
        """Length 0 should return an empty string without raising."""
        assert generate_code(length=0) == ""


class TestGenerateCodeCharset:
    def test_all_chars_are_base62(self):
        """Every character in a generated code must be in the base-62 alphabet."""
        code = generate_code(length=50)
        assert all(c in _BASE62 for c in code), f"Non-base62 char in: {code!r}"

    def test_no_special_characters(self):
        """Codes must be URL-safe: no hyphens, underscores, or symbols."""
        for _ in range(100):
            code = generate_code()
            assert code.isalnum(), f"Non-alphanumeric char in: {code!r}"


class TestGenerateCodeUniqueness:
    def test_uniqueness_across_1000_calls(self):
        """
        Generate 1000 codes and assert no collisions.

        With 62^7 ≈ 3.5 trillion possibilities and 1000 samples the birthday
        probability of any collision is ~1.4e-7 — a failure signals a broken RNG.
        """
        codes = {generate_code() for _ in range(1000)}
        assert len(codes) == 1000

    def test_two_consecutive_calls_differ(self):
        """Back-to-back calls must produce different codes with overwhelming probability."""
        results = {generate_code() for _ in range(10)}
        assert len(results) > 1
