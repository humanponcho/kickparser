import pytest
import pandas as pd
from parser_logic import clean_column_name, classify_columns, dedupe_column_names, build_label, build_items_list, strip_pii


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


class TestDedupeColumnNames:
    def test_no_duplicates_unchanged(self):
        assert dedupe_column_names(['A', 'B', 'C']) == ['A', 'B', 'C']

    def test_single_duplicate_gets_suffix(self):
        result = dedupe_column_names(['A', 'B', 'A'])
        assert result == ['A', 'B', 'A_1']

    def test_multiple_duplicates_increment(self):
        result = dedupe_column_names(['A', 'A', 'A'])
        assert result == ['A', 'A_1', 'A_2']

    def test_empty_list(self):
        assert dedupe_column_names([]) == []

    def test_realistic_addon_collision(self):
        # Two addon cols that clean to the same name
        cols = ['T-Shirt', 'T-Shirt', 'Poster']
        result = dedupe_column_names(cols)
        assert len(set(result)) == len(result)  # all unique


class TestBuildLabel:
    def _row(self, **kwargs):
        defaults = {
            'Shipping Name': 'Jane Doe',
            'Shipping Address 1': '123 Main St',
            'Shipping City': 'Springfield',
            'Shipping State': 'IL',
            'Shipping Postal Code': '62701',
            'Shipping Country Code': 'US',
        }
        defaults.update(kwargs)
        return defaults

    def test_full_row(self):
        label = build_label(self._row())
        assert label == "Jane Doe\n123 Main St\nSpringfield, IL  62701\nUS"

    def test_missing_state(self):
        label = build_label(self._row(**{'Shipping State': ''}))
        assert 'Springfield  62701' in label

    def test_missing_postal(self):
        label = build_label(self._row(**{'Shipping Postal Code': ''}))
        assert 'Springfield, IL' in label
        assert '  ' not in label.split('\n')[2]

    def test_missing_address1(self):
        label = build_label(self._row(**{'Shipping Address 1': ''}))
        lines = label.split('\n')
        assert 'Jane Doe' in lines[0]
        assert '123 Main St' not in label

    def test_nan_values_omitted(self):
        import math
        label = build_label(self._row(**{'Shipping State': float('nan')}))
        assert 'nan' not in label.lower()

    def test_empty_row_returns_empty_string(self):
        label = build_label({})
        assert label == ''

    def test_no_trailing_blank_lines(self):
        label = build_label(self._row(**{'Shipping Country Code': ''}))
        assert not label.endswith('\n')


class TestBuildItemsList:
    def _row(self, **kwargs):
        defaults = {
            'Reward Title': 'Deluxe Edition',
            '[Addon: 1] T-Shirt': 1,
            '[Addon: 2] Poster': 2,
            '[Addon: 3] Sticker Pack': 0,
        }
        defaults.update(kwargs)
        return defaults

    def _addon_cols(self):
        return ['[Addon: 1] T-Shirt', '[Addon: 2] Poster', '[Addon: 3] Sticker Pack']

    def test_reward_title_always_first(self):
        result = build_items_list(self._row(), self._addon_cols())
        assert result.startswith('- Deluxe Edition')

    def test_single_quantity_no_prefix(self):
        result = build_items_list(self._row(), self._addon_cols())
        assert '- T-Shirt' in result
        assert '1x' not in result

    def test_multi_quantity_shows_count(self):
        result = build_items_list(self._row(), self._addon_cols())
        assert '- 2x Poster' in result

    def test_zero_quantity_excluded(self):
        result = build_items_list(self._row(), self._addon_cols())
        assert 'Sticker' not in result

    def test_nan_addon_excluded(self):
        row = self._row(**{'[Addon: 1] T-Shirt': float('nan')})
        result = build_items_list(row, self._addon_cols())
        assert 'T-Shirt' not in result
        assert 'nan' not in result.lower()

    def test_no_addons_returns_reward_only(self):
        row = {'Reward Title': 'Basic', '[Addon: 1] T-Shirt': 0}
        result = build_items_list(row, ['[Addon: 1] T-Shirt'])
        assert result == '- Basic'

    def test_empty_row_returns_empty_string(self):
        result = build_items_list({}, [])
        assert result == ''

    def test_all_items_bulleted(self):
        result = build_items_list(self._row(), self._addon_cols())
        for line in result.split('\n'):
            assert line.startswith('- ')


class TestStripPii:
    def _make_df(self):
        return pd.DataFrame(columns=[
            'Backer Number', 'Backer Name', 'Email', 'Backer UID',
            'Reward Title', 'Pledge Amount', 'Pledged At', 'Fulfillment Status',
            'Shipping Country', 'Shipping Address 1', 'Shipping City',
            'Shipping State', 'Shipping Zip', 'Billing State', 'Notes',
        ])

    def test_pii_columns_removed(self):
        result = strip_pii(self._make_df())
        for col in ['Backer Name', 'Email', 'Backer UID', 'Shipping Address 1',
                    'Shipping City', 'Shipping State', 'Shipping Zip', 'Billing State', 'Notes']:
            assert col not in result.columns

    def test_safe_columns_kept(self):
        result = strip_pii(self._make_df())
        for col in ['Backer Number', 'Reward Title', 'Pledge Amount',
                    'Pledged At', 'Fulfillment Status', 'Shipping Country']:
            assert col in result.columns

    def test_all_safe_df_passes_through(self):
        df = pd.DataFrame(columns=['Reward Title', 'Pledge Amount', 'Shipping Country'])
        result = strip_pii(df)
        assert list(result.columns) == ['Reward Title', 'Pledge Amount', 'Shipping Country']

    def test_all_pii_df_returns_empty_columns(self):
        df = pd.DataFrame(columns=['Backer Name', 'Email', 'Shipping Address 1'])
        result = strip_pii(df)
        assert len(result.columns) == 0
