import pytest
import pandas as pd
from parser_logic import (clean_column_name, classify_columns, dedupe_column_names,
                          build_label, build_items_list, strip_pii,
                          detect_format, normalise_bigcartel, parse_bigcartel_items)


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


class TestDetectFormat:
    def test_detects_kickstarter(self):
        df = pd.DataFrame(columns=['Backer Number', 'Backer Name', 'Reward Title'])
        assert detect_format(df) == 'kickstarter'

    def test_detects_bigcartel(self):
        df = pd.DataFrame(columns=['Number', 'Buyer first name', 'Buyer last name'])
        assert detect_format(df) == 'bigcartel'

    def test_unknown_format_defaults_to_kickstarter(self):
        df = pd.DataFrame(columns=['Col A', 'Col B'])
        assert detect_format(df) == 'kickstarter'


class TestParseBigCartelItems:
    SINGLE = "product_name:Breakwater by Katriona Chapman|product_option_name:|quantity:1|price:12.99|total:12.99"
    MULTI  = (
        "product_name:Breakwater by Katriona Chapman|product_option_name:|quantity:1|price:12.99|total:12.99;"
        "product_name:Acid Box|product_option_name:|quantity:2|price:14.99|total:29.98"
    )

    def test_single_item(self):
        result = parse_bigcartel_items(self.SINGLE)
        assert '- Breakwater by Katriona Chapman' in result

    def test_single_quantity_no_count_prefix(self):
        result = parse_bigcartel_items(self.SINGLE)
        assert '1x' not in result

    def test_multi_item_separator(self):
        result = parse_bigcartel_items(self.MULTI)
        assert 'Breakwater' in result
        assert 'Acid Box' in result

    def test_multi_quantity_shows_count(self):
        result = parse_bigcartel_items(self.MULTI)
        assert '2x Acid Box' in result

    def test_empty_string_returns_empty(self):
        assert parse_bigcartel_items('') == ''

    def test_nan_returns_empty(self):
        assert parse_bigcartel_items('nan') == ''

    def test_all_lines_bulleted(self):
        result = parse_bigcartel_items(self.MULTI)
        for line in result.strip().split('\n'):
            assert line.startswith('- ')


class TestNormaliseBigCartel:
    def _make_df(self):
        return pd.DataFrame([{
            'Number': 'XCRB-630287',
            'Buyer first name': 'Ron',
            'Buyer last name': 'Evans',
            'Buyer email': 'ron@example.com',
            'Buyer phone number': '+1 415 000 0000',
            'Date': '2026-05-26',
            'Time': '4:56 AM BST',
            'Status': '',
            'Payment status': 'completed',
            'Transaction ID': 'pi_abc',
            'Shipping status': 'unshipped',
            'Shipping methods': 'Shipping :7.0',
            'Shipping address 1': '76 Indian Rock Road',
            'Shipping address 2': '',
            'Shipping city': 'San Anselmo',
            'Shipping state': 'California',
            'Shipping zip': '94960',
            'Shipping country': 'US',
            'Currency': 'GBP',
            'Items': 'product_name:Breakwater by Katriona Chapman|product_option_name:|quantity:1|price:12.99|total:12.99',
            'Item count': 1,
            'Item total': 12.99,
            'Total price': 19.99,
            'Total shipping': 7.0,
            'Total tax': 0.0,
            'Tax remitted by Big Cartel': 0,
            'Total discount': 0.0,
            'Discount code': 'SAVE10',
            'Source': 'Online',
            'Note': '',
            'Private notes': '',
        }])

    def test_required_output_columns_present(self):
        result = normalise_bigcartel(self._make_df())
        for col in ['Backer Number', 'Backer Name', 'Email', 'Reward Title',
                    'Pledge Amount', 'Shipping Country', 'Items']:
            assert col in result.columns

    def test_name_concatenated(self):
        result = normalise_bigcartel(self._make_df())
        assert result['Backer Name'].iloc[0] == 'Ron Evans'

    def test_shipping_name_matches_backer_name(self):
        result = normalise_bigcartel(self._make_df())
        assert result['Shipping Name'].iloc[0] == 'Ron Evans'

    def test_address_parts_in_full_address(self):
        result = normalise_bigcartel(self._make_df())
        addr = result['Shipping Full Address'].iloc[0]
        assert '76 Indian Rock Road' in addr
        assert 'San Anselmo' in addr
        assert 'US' in addr

    def test_addr2_combined_into_addr1(self):
        df = self._make_df()
        df.at[0, 'Shipping address 2'] = 'Apt 4'
        result = normalise_bigcartel(df)
        assert 'Apt 4' in result['Shipping Address 1'].iloc[0]

    def test_reward_title_is_first_product(self):
        result = normalise_bigcartel(self._make_df())
        assert result['Reward Title'].iloc[0] == 'Breakwater by Katriona Chapman'

    def test_items_parsed_and_bulleted(self):
        result = normalise_bigcartel(self._make_df())
        assert result['Items'].iloc[0].startswith('- ')

    def test_discount_code_preserved(self):
        result = normalise_bigcartel(self._make_df())
        assert result['Discount Code'].iloc[0] == 'SAVE10'
