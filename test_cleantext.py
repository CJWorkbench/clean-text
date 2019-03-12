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
    'type_char': 'nop',
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
        params = {'colnames': '',
                  'type_space': 'trim_around',
                  'condense': True,
                  'type_caps': 'nop',
                  'type_char': 'nop'}
        out = render(self.table, params)
        self.assertTrue(out.equals(self.table))

    def test_NOP_leave_all_as_is(self):
        params = {'colnames': 'spacecol',
                  'type_space': 'nop',
                  'type_caps': 'nop',
                  'type_char': 'nop'}
        out = render(self.table, params)
        self.assertTrue(out.equals(self.table))

    def test_spaces(self):
        # spacecol should only contain 'helloworld'
        params = {'colnames': 'spacecol',
                  'type_space': 'remove_all',
                  'type_caps': 'nop',
                  'type_char': 'nop'}
        out = render(self.table.copy(), params)
        for y in out['spacecol']:
            self.assertEqual(y, 'helloworld')

        # Test condense
        params = {'colnames': 'spacecol',
                  'type_space': 'trim_around',
                  'condense': True,
                  'type_caps': 'nop',
                  'type_char': 'nop'}
        out = render(self.table.copy(), params)
        for y in out['spacecol']:
            self.assertEqual(y, 'hello world')

        # Trim After
        params = {'colnames': 'spacecol',
                  'type_space': 'trim_after',
                  'condense': True,
                  'type_caps': 'nop',
                  'type_char': 'nop'}

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
        params = {'colnames': 'spacecol',
                  'type_space': 'trim_before',
                  'condense': False,
                  'type_caps': 'nop',
                  'type_char': 'nop'}

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
        params = {'colnames': 'special',
                  'type_space': 'remove_all',
                  'type_caps': 'upper',
                  'type_char': 'keep',
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
        params = {'colnames': 'spacecol',
                  'type_space': 'trim_around',
                  'condense': True,
                  'type_caps': 'nop',
                  'type_char': 'delete',
                  'letter': False,
                  'number': False,
                  'punc': False,
                  'custom': True,
                  'chars': 'l'}

        out = render(self.table.copy(), params)
        for y in out['spacecol']:
            self.assertEqual(y, 'heo word')

        # space should only contain 'heo word'
        params = {'colnames': 'floatcol',
                  'type_space': 'remove_all',
                  'type_caps': 'nop',
                  'type_char': 'delete',
                  'letter': False,
                  'number': False,
                  'punc': False,
                  'custom': True,
                  'chars': '23a.'}

        out = render(self.table.copy(), params)
        for y in out['floatcol']:
            self.assertEqual(y, '1')

    def test_punc(self):
        df = pd.DataFrame({
            'A': [' 2, 0, 0. 1 ', '20.01', ' 2 0 0 1\t',
                  '2.001', ',,2..001 \t'],
        }, dtype='category')

        result = render(df, {
            **DefaultParams,
            'colnames': 'A',
            'type_space': 'remove_all',
            'type_char': 'delete',
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
        params = {'colnames': 'spacecol',
                  'type_space': 'trim_around',
                  'condense': True,
                  'type_caps': 'upper',
                  'type_char': 'nop'}
        out = render(self.table.copy(), params)
        for y in out['spacecol']:
            self.assertEqual(y, 'HELLO WORLD')

        # 'hello world'
        params['type_caps'] = 'lower'
        out = render(out, params)
        for y in out['spacecol']:
            self.assertEqual(y, 'hello world')

    def test_multi_char_keep(self):
        params = {'colnames': 'catcol,spacecol',
                  'type_space': 'remove_all',
                  'type_caps': 'nop',
                  'type_char': 'keep',
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
        params = {'colnames': 'catcol,spacecol',
                  'type_space': 'remove_all',
                  'type_caps': 'nop',
                  'type_char': 'delete',
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

    def test_null(self):
        # null result
        params = {'colnames': 'nullcol',
                  'type_space': 'remove_all',
                  'type_caps': 'upper',
                  'type_char': 'delete',
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

    def test_migrate_v0_to_v1(self):
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
        self.assertEqual(new_params['type_char'], 'delete')

if __name__ == '__main__':
    unittest.main()
