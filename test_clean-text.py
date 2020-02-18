import datetime
import unittest
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import importlib

render = importlib.import_module("clean-text").render
migrate_params = importlib.import_module("clean-text").migrate_params

DefaultParams = {
    'colnames': [],
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


def P(**kwargs):
    """Build a params dict."""
    return {
        **DefaultParams,
        **kwargs
    }


class TestCleanText(unittest.TestCase):
    def test_initial_nop(self):
        # should NOP when first applied; no column selected
        result = render(pd.DataFrame({'A': [' x', ' y']}), P())
        assert_frame_equal(result, pd.DataFrame({'A': [' x', ' y']}))

    def test_space_nop(self):
        result = render(pd.DataFrame({'A': [' x', ' y']}),
                        P(colnames=['A'], type_space='nop'))
        assert_frame_equal(result, pd.DataFrame({'A': [' x', ' y']}))

    def test_space_remove_all(self):
        result = render(pd.DataFrame({
            'A': ['\t \x09a \x0a b     \r', np.nan, ' ', 'x'],
        }), P(colnames=['A'], type_space='remove_all'))
        assert_frame_equal(result,
                           pd.DataFrame({'A': ['ab', np.nan, '', 'x']}))

    def test_space_trim_around(self):
        result = render(pd.DataFrame({
            'A': ['\t \ta \n b     \r', np.nan, ' ', 'x'],
        }), P(colnames=['A'], type_space='trim_around'))
        assert_frame_equal(result,
                           pd.DataFrame({'A': ['a \n b', np.nan, '', 'x']}))

    def test_space_trim_after(self):
        result = render(pd.DataFrame({
            'A': ['\t \ta \n b     \r', np.nan, ' ', 'x'],
        }), P(colnames=['A'], type_space='trim_after'))
        assert_frame_equal(
            result,
            pd.DataFrame({'A': ['\t \ta \n b', np.nan, '', 'x']})
        )

    def test_space_trim_before(self):
        result = render(pd.DataFrame({
            'A': ['\t \ta \n b  \r', np.nan, ' ', 'x'],
        }), P(colnames=['A'], type_space='trim_before'))
        assert_frame_equal(
            result,
            pd.DataFrame({'A': ['a \n b  \r', np.nan, '', 'x']})
        )

    def test_condense(self):
        result = render(pd.DataFrame({
            'A': ['\t \ta \n b     \r', np.nan, ' ', 'x'],
        }), P(colnames=['A'], type_space='nop', condense=True))
        assert_frame_equal(result,
                           pd.DataFrame({'A': [' a b ', np.nan, ' ', 'x']}))

    def test_letters_keep_and_caps_upper(self):
        result = render(pd.DataFrame({
            'A': ['café', '\t..谢 谢 你123    ', '\x0Chello©world', 'àçñ',
                  ' Æ !@!@! Ï ']
        }),
            P(colnames=['A'], type_space='remove_all', type_caps='upper',
              type_char=True, letter=True)
        )
        assert_frame_equal(result, pd.DataFrame({
            'A': ['CAFÉ', '谢谢你', 'HELLOWORLD', 'ÀÇÑ', 'ÆÏ'],
        }))

    def test_letters_keep_and_caps_lower(self):
        result = render(pd.DataFrame({
            'A': ['café', '\t..谢 谢 你123    ', '\x0Chello©world', 'àçñ',
                  ' Æ !@!@! Ï ']
        }),
            P(colnames=['A'], type_space='remove_all', type_caps='lower',
              type_char=True, letter=True)
        )
        assert_frame_equal(result, pd.DataFrame({
            'A': ['café', '谢谢你', 'helloworld', 'àçñ', 'æï'],
        }))

    def test_delete_custom(self):
        result = render(pd.DataFrame({
            'A': ['hello', 'world', np.nan],
        }), P(colnames=['A'], type_char=False, custom=True, chars='lo'))
        assert_frame_equal(result, pd.DataFrame({'A': ['he', 'wrd', np.nan]}))

    def test_custom_special_regex_characters(self):
        table = pd.DataFrame({'A': ['John, Marshall, Jr.']})
        result = render(table, P(
            colnames=['A'],
            custom=True,
            type_char=False,  # delete
            chars=r',\sJr.',  # "\" and "s" are two characters, not regex
        ))
        assert_frame_equal(result, pd.DataFrame({'A': ['ohn Mahall']}))

    def test_punc(self):
        df = pd.DataFrame({
            'A': [' 2, 0, 0. 1 ', '20.01', ' 2 0 0 1\t',
                  '2.001', ',,2..001 \t'],
        }, dtype='category')

        result = render(df, {
            **DefaultParams,
            'colnames': ['A'],
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

    def test_char_keep(self):
        result = render(pd.DataFrame({
            'A': ['2.0', 'café', '@hey-yo'],
        }), P(
            colnames=['A'],
            type_space='nop',
            type_char=True,  # keep
            letter=True,
            number=True,
            punc=False,
            custom=False,
        ))
        assert_frame_equal(result,
                           pd.DataFrame({'A': ['20', 'café', 'heyyo']}))

    def test_char_delete(self):
        result = render(pd.DataFrame({
            'A': ['2.0', 'café', '@hey, yo'],
        }), P(
            colnames=['A'],
            type_space='nop',
            type_char=False,  # delete
            letter=False,
            number=False,
            punc=True,
            custom=False,
        ))
        assert_frame_equal(result,
                           pd.DataFrame({'A': ['20', 'café', 'hey yo']}))

    def test_delete_nothing(self):
        # should be a NOP
        result = render(pd.DataFrame({
            'A': ['2.0', 'café', '@hey, yo'],
        }), P(
            colnames=['A'],
            type_space='nop',
            type_char=False,  # delete
            letter=False,
            number=False,
            punc=False,
            custom=False,
        ))
        assert_frame_equal(result,
                           pd.DataFrame({'A': ['2.0', 'café', '@hey, yo']}))

    def test_merge_categories(self):
        result = render(
            pd.DataFrame({'A': [' x', 'x ', ' x ', 'y', np.nan]},
                         dtype='category'),
            P(colnames=['A'], type_space='remove_all')
        )
        assert_frame_equal(
            result,
            pd.DataFrame({'A': ['x', 'x', 'x', 'y', np.nan]}, dtype='category')
        )


class MigrateParamsTest(unittest.TestCase):
    def test_migrate_v0(self):
        self.assertEqual(migrate_params({
            'colnames': 'floatcol',
            'type_space': 3,  # v0: old-style menu
            'type_caps': 2,  # v0: old-style menu
            'type_char': 1,  # v0: old-style menu
            'letter': False,
            'number': False,
            'punc': False,
            'custom': True,
            'chars': '23a.'
        }), {
            'colnames': ['floatcol'],
            'type_space': 'remove_all',
            'type_caps': 'lower',
            'type_char': False,
            'letter': False,
            'number': False,
            'punc': False,
            'custom': True,
            'chars': '23a.'
        })

    def test_migrate_v1_type_char_nop(self):
        # v2 is uses radio button keep/delete so only True/False 
        # Migration translates NOP to delete w/ with nothing selected
        self.assertEqual(migrate_params({
            'colnames': 'floatcol',
            'type_space': 'nop',
            'type_caps': 'nop',
            'type_char': 'nop',  # v1: obsolete option, means "delete nothing"
            'letter': True,
            'number': False,
            'punc': False,
            'custom': True,
            'chars': '23a.'
        }), {
            'colnames': ['floatcol'],
            'type_space': 'nop',
            'type_caps': 'nop',
            'type_char': False,  # delete
            # letter/number/punc/custom all empty
            'letter': False,
            'number': False,
            'punc': False,
            'custom': False,
            'chars': '23a.'
        })

    def test_migrate_v1(self):
        # v2 is uses radio button keep/delete so only True/False 
        # Migration translates NOP to delete w/ with nothing selected
        self.assertEqual(migrate_params({
            'colnames': 'floatcol',
            'type_space': 'nop',
            'type_caps': 'nop',
            'type_char': 'delete',  # v1: obsolete option, means "delete nothing"
            'letter': True,
            'number': False,
            'punc': False,
            'custom': True,
            'chars': '23a.'
        }), {
            'colnames': ['floatcol'],
            'type_space': 'nop',
            'type_caps': 'nop',
            'type_char': False,  # delete
            # these shouldn't be modified
            'letter': True,
            'number': False,
            'punc': False,
            'custom': True,
            'chars': '23a.'
        })

    def test_migrate_v2_no_colnames(self):
        self.assertEqual(migrate_params({
            'colnames': '',  # v2: colnames are comma-separated str
            'type_space': 'nop',
            'type_caps': 'nop',
            'type_char': False,
            'letter': True,
            'number': False,
            'punc': False,
            'custom': True,
            'chars': '23a.'
        }), {
            'colnames': [],
            'type_space': 'nop',
            'type_caps': 'nop',
            'type_char': False,
            'letter': True,
            'number': False,
            'punc': False,
            'custom': True,
            'chars': '23a.'
        })

    def test_migrate_v2(self):
        self.assertEqual(migrate_params({
            'colnames': 'A,B',  # v2: colnames are comma-separated str
            'type_space': 'nop',
            'type_caps': 'nop',
            'type_char': False,
            'letter': True,
            'number': False,
            'punc': False,
            'custom': True,
            'chars': '23a.'
        }), {
            'colnames': ['A', 'B'],
            'type_space': 'nop',
            'type_caps': 'nop',
            'type_char': False,
            'letter': True,
            'number': False,
            'punc': False,
            'custom': True,
            'chars': '23a.'
        })


if __name__ == '__main__':
    unittest.main()
