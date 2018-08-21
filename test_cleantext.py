import unittest
import pandas as pd
from cleantext import render

space_map = 'Trim around value|Trim before value|Trim after value|Remove all spaces|Leave as is'.lower().split('|')
caps_map  = 'Leave as is|Uppercase|Lowercase'.lower().split('|')
char_map = 'Keep all|Drop|Keep'.lower().split('|')

class TestCleanText(unittest.TestCase):

    def setUp(self):
        # Individual Cases
        self.table = pd.DataFrame([
            ['\t  hello  world     \n', 1.23, 'a 133 aaa', '\x0A1Aa^&\x0A*^*2---3\x0A', ' 2, 0, 0. 1 ', 'café', None],
            ['hello world', 12.3, 3313, ',,1..\x0A.2\x09 nn3', 20.01, '\t..谢 谢 你123    ', 1.2],
            ['\thello\t\tworld\t', -1.23, 231.33, '<\x09 1   !@$@%^@^&*23\x09 \x09 >', ' 2 0 0 1\t', '\x0Chello©world', ''],
            ['hello    world     ', 12.3, ' a1.22 ', '??12\xC03', 2.001, 'àçñ', '\t\n !@##! 123123 asadas'],
            [' \x09   hello \x0A world   \x0A', 1.23, 13, '123@.com', ',,2..001  \t', ' Æ !@!@! Ï ', 'abc']],
            columns=['spacecol', 'numcol1', 'floatcol', 'numcol2', 'catcol', 'special', 'nullcol'])

        # Special Cases

        self.table['catcol'] = self.table['catcol'].astype('category')
        self.table['floatcol'] = self.table['floatcol'].astype('category')
        self.table['nullcol'] = self.table['nullcol'].astype('category')

    def test_NOP(self):
        params = {'colnames': '',
                  'type_space': space_map.index('trim around value'),
                  'condense': True,
                  'type_caps': caps_map.index('leave as is'),
                  'type_char': char_map.index('keep all')}
        out = render(self.table, params)
        self.assertTrue(out.equals(self.table))  # should NOP when first applied

        params = {'colnames': 'spacecol',
                  'type_space': space_map.index('leave as is'),
                  'type_caps': caps_map.index('leave as is'),
                  'type_char': char_map.index('keep all')}
        out = render(self.table, params)
        self.assertTrue(out.equals(self.table))

    def test_spaces(self):
        # spacecol should only contain 'helloworld'
        params = {'colnames': 'spacecol',
                  'type_space': space_map.index('remove all spaces'),
                  'type_caps': caps_map.index('leave as is'),
                  'type_char': char_map.index('keep all')}
        out = render(self.table.copy(), params)
        for y in out['spacecol']:
            self.assertTrue(y == 'helloworld')

        # Test condense
        params = {'colnames': 'spacecol',
                  'type_space': space_map.index('trim around value'),
                  'condense': True,
                  'type_caps': caps_map.index('leave as is'),
                  'type_char': char_map.index('keep all')}
        out = render(self.table.copy(), params)
        for y in out['spacecol']:
            self.assertTrue(y == 'hello world')

        # Trim After
        params = {'colnames': 'spacecol',
                  'type_space': space_map.index('trim after value'),
                  'condense': True,
                  'type_caps': caps_map.index('leave as is'),
                  'type_char': char_map.index('keep all')}

        out = render(self.table.copy(), params)
        ref = self.table.copy()
        ref['spacecol'] = pd.Series(
            ['\t  hello world', 'hello world', '\thello world', 'hello world', ' \x09   hello world'])
        pd.testing.assert_frame_equal(out, ref)

        # Trim Before and condense False
        params = {'colnames': 'spacecol',
                  'type_space': space_map.index('trim before value'),
                  'condense': False,
                  'type_caps': caps_map.index('leave as is'),
                  'type_char': char_map.index('keep all')}

        out = render(self.table.copy(), params)
        ref = self.table.copy()
        ref['spacecol'] = pd.Series(
            ['hello  world     \n', 'hello world', 'hello\t\tworld\t', 'hello    world     ', 'hello \x0A world   \x0A'])
        pd.testing.assert_frame_equal(out, ref)

    def test_letters(self):
        # Keep letters and uppercase
        params = {'colnames': 'special',
                  'type_space': space_map.index('remove all spaces'),
                  'type_caps': caps_map.index('uppercase'),
                  'type_char': char_map.index('keep'),
                  'letter': True,
                  'number': False,
                  'punc': False,
                  'custom': False,
                  'chars': ''}

        out = render(self.table.copy(), params)
        ref = self.table.copy()
        ref['special'] = pd.Series(
            ['CAFÉ', '谢谢你', 'HELLOWORLD', 'ÀÇÑ','ÆÏ'])
        pd.testing.assert_frame_equal(out, ref)

        params['type_caps'] = caps_map.index('lowercase')
        out = render(self.table.copy(), params)
        ref['special'] = pd.Series(
            ['café', '谢谢你', 'helloworld', 'àçñ', 'æï'])
        pd.testing.assert_frame_equal(out, ref)

    def test_numbers(self):
        # numcol should only contain '123'
        params = {'colnames': 'numcol1,numcol2',
                  'type_space': space_map.index('remove all spaces'),
                  'type_caps': caps_map.index('leave as is'),
                  'type_char': char_map.index('keep'),
                  'letter': False,
                  'number': True,
                  'punc': False,
                  'custom': False,
                  'chars': ''}

        out = render(self.table.copy(), params)
        for y in out['numcol1']:
            self.assertTrue(y == '123')
        for y in out['numcol2']:
            self.assertTrue(y == '123')

        # Drop numbers and '-', expect all '.'
        params = {'colnames': 'numcol1',
                  'type_space': space_map.index('remove all spaces'),
                  'type_caps': caps_map.index('leave as is'),
                  'type_char': char_map.index('drop'),
                  'letter': False,
                  'number': True,
                  'punc': False,
                  'custom': True,
                  'chars': '-'}

        out = render(self.table.copy(), params)
        ref = self.table.copy()
        ref['numcol1'] = pd.Series(['.']*5)
        pd.testing.assert_frame_equal(out, ref)

    def test_custom(self):
        # space should only contain 'heo word'
        params = {'colnames': 'spacecol',
                  'type_space': space_map.index('trim around value'),
                  'condense': True,
                  'type_caps': caps_map.index('leave as is'),
                  'type_char': char_map.index('drop'),
                  'letter': False,
                  'number': False,
                  'punc': False,
                  'custom': True,
                  'chars': 'l'}

        out = render(self.table.copy(), params)
        for y in out['spacecol']:
            self.assertTrue(y == 'heo word')

        # space should only contain 'heo word'
        params = {'colnames': 'floatcol',
                  'type_space': space_map.index('remove all spaces'),
                  'type_caps': caps_map.index('leave as is'),
                  'type_char': char_map.index('drop'),
                  'letter': False,
                  'number': False,
                  'punc': False,
                  'custom': True,
                  'chars': '23a.'}

        out = render(self.table.copy(), params)
        for y in out['floatcol']:
            self.assertTrue(y == '1')

    def test_punc(self):
        # catcol should only contain 2001
        params = {'colnames': 'catcol',
                  'type_space': space_map.index('remove all spaces'),
                  'type_caps': caps_map.index('leave as is'),
                  'type_char': char_map.index('drop'),
                  'letter': False,
                  'number': False,
                  'punc': True,
                  'custom': False,
                  'chars': ''}

        out = render(self.table.copy(), params)
        for y in out['catcol']:
            self.assertTrue(y == '2001')

    def test_case(self):
        # 'HELLO WORLD'
        params = {'colnames': 'spacecol',
                  'type_space': space_map.index('trim around value'),
                  'condense': True,
                  'type_caps': caps_map.index('uppercase'),
                  'type_char': char_map.index('keep all')}
        out = render(self.table.copy(), params)
        for y in out['spacecol']:
            self.assertTrue(y == 'HELLO WORLD')

        # 'hello world'
        params['type_caps'] = caps_map.index('lowercase')
        out = render(out, params)
        for y in out['spacecol']:
            self.assertTrue(y == 'hello world')

    def test_null(self):
        # null result
        params = {'colnames': 'nullcol',
                  'type_space': space_map.index('remove all spaces'),
                  'type_caps': caps_map.index('uppercase'),
                  'type_char': char_map.index('drop'),
                  'letter': False,
                  'number': False,
                  'punc': False,
                  'custom': True,
                  'chars': '!@#123abcds.'}
        out = render(self.table.copy(), params)
        for y in out['nullcol']:
            self.assertTrue(not y or pd.isna(y))
if __name__ == '__main__':
    unittest.main()
