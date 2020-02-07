# -*- coding: utf-8 -*-
import re


# Define characters by regex
unicode_cat_map = {
    'number': r'\d',
    'letter': r'^\W\d_',
    'punc':     '!-#%-*,-/:-;?-@[-\]_{}¡«·»¿;·՚-՟։-֊־׀׃׆׳-״؉-؊،-؍؛؞-؟٪-٭۔܀-܍߷-߹।-॥' \
                '॰෴๏๚-๛༄-༒༺-༽྅࿐-࿔၊-၏჻፡-፨᙭-᙮᚛-᚜᛫-᛭᜵-᜶។-៖៘-៚᠀-᠊᥄-᥅᧞-᧟᨞-᨟᭚-᭠᰻-᰿᱾-᱿\u2000-\u206e' \
                '⁽-⁾₍-₎〈-〉❨-❵⟅-⟆⟦-⟯⦃-⦘⧘-⧛⧼-⧽⳹-⳼⳾-⳿⸀-\u2e7e\u3000-〾゠・꘍-꘏꙳꙾꡴-꡷꣎-꣏꤮-꤯꥟꩜-꩟﴾-﴿︐-︙︰-﹒﹔' \
                '-﹡﹣﹨﹪-﹫！-＃％-＊，-／：-；？-＠［-］＿｛｝｟-･'

}

space_regex_map = {
    'trim_before': r'^[\s]+',
    'trim_after': r'[\s]+$',
    'trim_around': r'^[\s]+|[\s]+$',
    'remove_all': r'[\s]'
}


def _migrate_params_v0_to_v1(params):
    """v0: menus use item indices. v1: menus use values."""
    v1_space_items = ['trim_around', 'trim_before', 'trim_after', 'remove_all',
                      'nop']
    v1_caps_items = ['nop','upper','lower']
    v1_char_items = ['nop','delete','keep']
    return {
        **params,
        'type_space': v1_space_items[params['type_space']],
        'type_caps': v1_caps_items[params['type_caps']],
        'type_char': v1_char_items[params['type_char']],
    }

def _migrate_params_v1_to_v2(params):
    """
    v1: type_char is menu and 'nop' is an option.

    v2: there is no 'nop'. Migrate to "delete nothing" (synonym).
    """
    if params['type_char'] == 'nop':
        # v2 represents 'nop' by deleting nothing
        return {
            **params,
            'type_char': False,
            'letter': False,
            'number': False,
            'punc': False,
            'custom': False,
        }
    else:
        return {
            **params,
            'type_char': params['type_char'] == 'keep'
        }


def _migrate_params_v2_to_v3(params):
    """v2: colnames are comma-separated str; v3: List[str]."""
    return {
        **params,
        'colnames': [c for c in params['colnames'].split(',') if c],
    }


def migrate_params(params):
    # Convert numeric menu parameters to string labels, if needed
    if isinstance(params['type_space'], int):
        params = _migrate_params_v0_to_v1(params)
    if isinstance(params['type_char'], str):
        params = _migrate_params_v1_to_v2(params)
    if isinstance(params['colnames'], str):
        params = _migrate_params_v2_to_v3(params)

    return params



def change_case(case, series):
    if case == 'upper':
        return series.str.upper()
    elif case == 'lower':
        return series.str.lower()


def build_regex(type, char_cats, char_custom):
    pattern_list = []
    if type == 'delete':
        if char_cats:
            for char in char_cats:
                pattern_list.append(f'[{char}]')
        if char_custom:
            pattern_list.append(f'[{re.escape(char_custom)}]')
        return re.compile('|'.join(pattern_list), re.UNICODE)
    else:
        # Keep spaces in all scenarios
        pattern = r'(?!\s)'
        # To drop all else, set char regex in negative lookahead then drop all
        # else [\d\D]
        if char_cats:
            for char in char_cats:
                pattern += f'(?![{char}])'
        if char_custom:
            escaped = re.escape(char_custom)
            pattern += f'(?![{escaped}])'
        pattern += r'[\d\D]'
        return re.compile(pattern, re.UNICODE)


def dispatch(space_params, type_caps, series, pattern=None):
    if pattern:
        series = series.str.replace(pattern, '')
    if space_params['type'] != 'nop':
        series = series.str.replace(space_regex_map[space_params['type']], '')
    if space_params['condense']:
        series = series.str.replace(r'[\s]+', ' ')
    if type_caps != 'nop':
        series = change_case(type_caps, series)

    return series

def render(table, params):
    # No processing if parameters define no change
    if not params['colnames'] or (
            params['type_space'] == 'nop'
            and params['type_caps'] == 'nop'
            and params['type_char'] == 'nop'):
        return table

    space_params = {
        'type': params['type_space']
    }

    type_caps = params['type_caps']

    # Space trimming
    if space_params['type'] != 'remove_all':
        space_params['condense'] = params['condense']
    else:
        space_params['condense'] = False

    # Build a set of unicode strings representing chosen character classes
    char_cats = []
    for char_cat in unicode_cat_map.keys():
        if params[char_cat]:
            char_cats.append(unicode_cat_map[char_cat])

    if params['custom']:
        char_custom = params['chars']
    else:
        char_custom = None

    # Are we modifying the set of characters in any way? Answer is no only if
    # we are deleting nothing
    keep_delete = 'keep' if params['type_char'] else 'delete'
    if keep_delete == 'keep' or char_cats or char_custom:
        pattern = build_regex(keep_delete, char_cats, char_custom)
    else:
        pattern = None

    for column in params['colnames']:
        series = table[column]
        new_series = dispatch(space_params, type_caps, series, pattern)

        if hasattr(series, 'cat'):
            # input was categorical; give categorical output
            # TODO clean the categories instead. (It's a mind-bender.)
            new_series = new_series.astype('category')

        table[column] = new_series

    return table
