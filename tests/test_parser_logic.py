import pytest
from parser_logic import clean_column_name, classify_columns


class TestCleanColumnName:
    def test_strips_addon_prefix(self):
        assert clean_column_name("[Addon: 3] T-Shirt") == "T-Shirt"

    def test_strips_addon_prefix_with_space(self):
        assert clean_column_name("[Addon: 12]  Extra Copy") == "Extra_Copy"

    def test_replaces_spaces_with_underscores(self):
        assert clean_column_name("Backer Name") == "Backer_Name"

    def test_removes_special_characters(self):
        assert clean_column_name("Col!@#Name") == "ColName"

    def test_replaces_by_with_dash(self):
        assert clean_column_name("Art by Artist") == "Art_-_Artist"

    def test_normalises_curly_apostrophe(self):
        result = clean_column_name("Don’t Miss It")
        assert "'" in result or "Dont" in result

    def test_collapses_multiple_spaces(self):
        assert clean_column_name("Too  Many   Spaces") == "Too_Many_Spaces"

    def test_strips_leading_trailing_whitespace(self):
        assert clean_column_name("  padded  ") == "padded"

    def test_plain_column_unchanged_structure(self):
        assert clean_column_name("Email") == "Email"


class TestClassifyColumns:
    def _make_columns(self):
        return [
            'Backer Number', 'Backer UID', 'Backer Name', 'Email',
            'Reward Title', 'Pledge Amount', 'Pledged At', 'Fulfillment Status',
            'Shipping Country', 'Shipping Address 1', 'Shipping City',
            '[Addon: 1] T-Shirt', '[Addon: 2] Poster',
        ]

    def test_core_columns_detected(self):
        core, _, _ = classify_columns(self._make_columns())
        assert 'Backer Number' in core
        assert 'Email' in core
        assert 'Reward Title' in core

    def test_shipping_columns_detected(self):
        _, shipping, _ = classify_columns(self._make_columns())
        assert 'Shipping Country' in shipping
        assert 'Shipping Address 1' in shipping

    def test_addon_columns_are_residual(self):
        _, _, addons = classify_columns(self._make_columns())
        assert '[Addon: 1] T-Shirt' in addons
        assert '[Addon: 2] Poster' in addons

    def test_no_column_appears_in_two_groups(self):
        cols = self._make_columns()
        core, shipping, addons = classify_columns(cols)
        all_classified = core + shipping + addons
        assert len(all_classified) == len(set(all_classified)), "Duplicate column in classification"

    def test_all_columns_classified(self):
        cols = self._make_columns()
        core, shipping, addons = classify_columns(cols)
        assert sorted(core + shipping + addons) == sorted(cols)

    def test_empty_columns_returns_empty_lists(self):
        core, shipping, addons = classify_columns([])
        assert core == shipping == addons == []

    def test_all_shipping_columns(self):
        cols = ['Shipping Name', 'Shipping Country', 'Shipping City']
        core, shipping, addons = classify_columns(cols)
        assert len(shipping) == 3
        assert core == []
        assert addons == []
