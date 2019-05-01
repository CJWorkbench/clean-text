import datetime
import unittest
import pandas as pd
from pandas.testing import assert_frame_equal
from cleantext import render, migrate_params

DefaultParams = {
    'colnames': '',
    'type_space': 'trim_around',
    'condense': False,
    'type_caps': 'nop',
    'type_char': False,  # keep/delete, false means delete
    'letter': False,
    'number': False,
    'punc': False,
    'custom': False,
    'chars': ''
}


class TestCleanText(unittest.TestCase):
    def setUp(self):
        # Individual Cases
        self.table = pd.DataFrame([
            ['\t  hello  world     \n', 'a 133 aaa', '\x0A1Aa^&\x0A*^*2---3\x0A', ' 2, 0, 0. 1 ', 'café', None],
            ['hello world', '3313', ',,1..\x0A.2\x09 nn3', '20.01', '\t..谢 谢 你123    ', '1.2'],
            ['\thello\t\tworld\t', '231.33', '<\x09 1   !@$@%^@^&*23\x09 \x09 >', ' 2 0 0 1\t', '\x0Chello©world', ''],
            ['hello    world     ', ' a1.22 ', '??12\xC03', '2.001', 'àçñ', '\t\n !@##! 123123 asadas'],
            [' \x09   hello \x0A world   \x0A', '13', '123@.com', ',,2..001  \t', ' Æ !@!@! Ï ', 'abc']],
            columns=['spacecol', 'floatcol', 'numcol2', 'catcol', 'special', 'nullcol'])

        # Special Cases

        self.table['catcol'] = self.table['catcol'].astype('category')
        self.table['nullcol'] = self.table['nullcol'].astype('category')

    def test_NOP(self):
        # should NOP when first applied; no column selected
        out = render(self.table, DefaultParams)
        self.assertTrue(out.equals(self.table))

    def test_NOP_leave_all_as_is(self):
        params = {**DefaultParams,
                  'colnames': 'spacecol'}
        out = render(self.table, params)
        self.assertTrue(out.equals(self.table))

    def test_spaces(self):
        # spacecol should only contain 'helloworld'
        params = {**DefaultParams,
                  'colnames': 'spacecol',
                  'type_space': 'remove_all'}
        out = render(self.table.copy(), params)
        for y in out['spacecol']:
            self.assertEqual(y, 'helloworld')

        # Test condense
        params = {**DefaultParams,
                  'colnames': 'spacecol',
                  'type_space': 'trim_around',
                  'condense': True }
        out = render(self.table.copy(), params)
        for y in out['spacecol']:
            self.assertEqual(y, 'hello world')

        # Trim After
        params = {**DefaultParams,
                  'colnames': 'spacecol',
                  'type_space': 'trim_after',
                  'condense': True }

        out = render(self.table.copy(), params)
        ref = self.table.copy()
        ref['spacecol'] = pd.Series([
            ' hello world',
            'hello world',
            ' hello world',
            'hello world',
            ' hello world'
        ])
        pd.testing.assert_frame_equal(out, ref)

        # Trim Before and condense False
        params = {**DefaultParams,
                  'colnames': 'spacecol',
                  'type_space': 'trim_before',
                  'condense': False }

        out = render(self.table.copy(), params)
        ref = self.table.copy()
        ref['spacecol'] = pd.Series([
            'hello  world     \n',
            'hello world',
            'hello\t\tworld\t',
            'hello    world     ',
            'hello \x0A world   \x0A'
        ])
        pd.testing.assert_frame_equal(out, ref)

    def test_letters(self):
        # Keep letters and uppercase
        params = {**DefaultParams,
                  'colnames': 'special',
                  'type_space': 'remove_all',
                  'type_caps': 'upper',
                  'type_char': True,  # keep
                  'letter': True,
                  'number': False,
                  'punc': False,
                  'custom': False,
                  'chars': ''}

        out = render(self.table.copy(), params)
        ref = self.table.copy()
        ref['special'] = pd.Series(
            ['CAFÉ', '谢谢你', 'HELLOWORLD', 'ÀÇÑ', 'ÆÏ'])
        pd.testing.assert_frame_equal(out, ref)

        params['type_caps'] = 'lower'
        out = render(self.table.copy(), params)
        ref['special'] = pd.Series(
            ['café', '谢谢你', 'helloworld', 'àçñ', 'æï'])
        pd.testing.assert_frame_equal(out, ref)

    def test_custom(self):
        # space should only contain 'heo word'
        params = {**DefaultParams,
                  'colnames': 'spacecol',
                  'type_space': 'trim_around',
                  'condense': True,
                  'type_caps': 'nop',
                  'type_char': False, # delete
                  'letter': False,
                  'number': False,
                  'punc': False,
                  'custom': True,
                  'chars': 'l'}

        out = render(self.table.copy(), params)
        for y in out['spacecol']:
            self.assertEqual(y, 'heo word')

        # space should only contain 'heo word'
        params = {**DefaultParams,
                  'colnames': 'floatcol',
                  'type_space': 'remove_all',
                  'type_caps': 'nop',
                  'type_char': False, # delete
                  'letter': False,
                  'number': False,
                  'punc': False,
                  'custom': True,
                  'chars': '23a.'}

        out = render(self.table.copy(), params)
        for y in out['floatcol']:
            self.assertEqual(y, '1')

    def test_custom_special_regex_characters(self):
        df = pd.DataFrame({'A': ['John, Marshall, Jr.']})
        result = render(df, {
            **DefaultParams,
            'colnames': 'A',
            'custom': True,
            'chars': r',\sJr.',  # "\" and "s" are two characters, not regex
            'type_char': False,
        })
        assert_frame_equal(result, pd.DataFrame({'A': ['ohn Mahall']}))

    def test_punc(self):
        df = pd.DataFrame({
            'A': [' 2, 0, 0. 1 ', '20.01', ' 2 0 0 1\t',
                  '2.001', ',,2..001 \t'],
        }, dtype='category')

        result = render(df, {
            **DefaultParams,
            'colnames': 'A',
            'type_space': 'remove_all',
            'type_char': False, # delete
            'letter': False,
            'number': False,
            'punc': True,
            'custom': False,
        })

        expected = pd.DataFrame(
            {'A': ['2001', '2001', '2001', '2001', '2001']},
            dtype='category'
        )
        assert_frame_equal(result, expected)

    def test_case(self):
        # 'HELLO WORLD'
        params = {**DefaultParams,
                  'colnames': 'spacecol',
                  'type_space': 'trim_around',
                  'condense': True,
                  'type_caps': 'upper'}
                  
        out = render(self.table.copy(), params)
        for y in out['spacecol']:
            self.assertEqual(y, 'HELLO WORLD')

        # 'hello world'
        params['type_caps'] = 'lower'
        out = render(out, params)
        for y in out['spacecol']:
            self.assertEqual(y, 'hello world')

    def test_multi_char_keep(self):
        params = {**DefaultParams,
                  'colnames': 'catcol,spacecol',
                  'type_space': 'remove_all',
                  'type_caps': 'nop',
                  'type_char': True,  # keep
                  'letter': True,
                  'number': True,
                  'punc': False,
                  'custom': False,
                  'chars': ''}

        out = render(self.table.copy(), params)
        for y in out['catcol']:
            self.assertEqual(y, '2001')

        for y in out['spacecol']:
            self.assertEqual(y, 'helloworld')

    def test_multi_char_drop(self):
        params = {**DefaultParams,
                  'colnames': 'catcol,spacecol',
                  'type_space': 'remove_all',
                  'type_caps': 'nop',
                  'type_char': False, # delete
                  'letter': False,
                  'number': False,
                  'punc': True,
                  'custom': False,
                  'chars': ''}

        out = render(self.table.copy(), params)
        for y in out['catcol']:
            self.assertEqual(y, '2001')

        for y in out['spacecol']:
            self.assertEqual(y, 'helloworld')

    def test_delete_nothing(self):
        # should be a NOP
        params = {**DefaultParams,
                  'colnames': 'special',
                  'type_space': 'nop',
                  'type_caps': 'nop',
                  'type_char': False, # delete
                  'letter': False,
                  'number': False,
                  'punc': False,
                  'custom': False,
                  'chars': ''}
        out = render(self.table.copy(), params)
        assert_frame_equal(out, self.table)

    def test_null_input_and_output(self):
        params = {**DefaultParams,
                  'colnames': 'nullcol',
                  'type_space': 'remove_all',
                  'type_caps': 'upper',
                  'type_char': False, # delete
                  'letter': False,
                  'number': False,
                  'punc': False,
                  'custom': True,
                  'chars': '!@#123abcds.'}
        out = render(self.table.copy(), params)
        for y in out['nullcol']:
            self.assertTrue(not y or pd.isna(y))

    def test_numbers_NOP(self):
        df = pd.DataFrame({'A': [1, 2]})
        result = render(df, {
            **DefaultParams,
            'colnames': 'A',
        })
        assert_frame_equal(result, pd.DataFrame({'A': [1, 2]}))

    def test_datetime_NOP(self):
        dt = datetime.datetime.now()
        df = pd.DataFrame({'A': [dt, dt]})
        result = render(df, {
            **DefaultParams,
            'colnames': 'A',
        })
        assert_frame_equal(result, pd.DataFrame({'A': [dt, dt]}))

    def test_migrate_v0_to_v2(self):
        params = {'colnames': 'floatcol',
                  'type_space': 3,
                  'type_caps': 2,
                  'type_char': 1,
                  'letter': False,
                  'number': False,
                  'punc': False,
                  'custom': True,
                  'chars': '23a.'}

        new_params = migrate_params(params)
        self.assertEqual(new_params['type_space'], 'remove_all')
        self.assertEqual(new_params['type_caps'], 'lower')
        self.assertEqual(new_params['type_char'], False) # delete

    def test_migrate_v1_to_v2(self):
        # v2 is uses radio button keep/delete so only True/False 
        # Migration translates NOP to delete w/ with nothing selected
        params = {'colnames': 'floatcol',
                  'type_space': 'nop',
                  'type_caps': 'nop',
                  'type_char': 'nop',
                  'letter': True,
                  'number': False,
                  'punc': False,
                  'custom': True,
                  'chars': '23a.'}

        new_params = migrate_params(params)
        self.assertEqual(new_params['type_char'], False) # delete
        self.assertFalse(new_params['letter'])
        self.assertFalse(new_params['number'])
        self.assertFalse(new_params['punc'])
        self.assertFalse(new_params['custom'])

if __name__ == '__main__':
    unittest.main()
