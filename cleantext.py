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
    # v0: menu item indices. v1: menu item labels
    v1_space_items = ['trim_around','trim_before','trim_after','remove_all','nop']
    params['type_space'] = v1_space_items[params['type_space']]

    v1_caps_items = ['nop','upper','lower']
    params['type_caps'] = v1_caps_items[params['type_caps']]

    v1_char_items = ['nop','delete','keep']
    params['type_char'] = v1_char_items[params['type_char']]

    return params


def migrate_params(params):
    # Convert numeric menu parameters to string labels, if needed
    if isinstance(params['type_space'], int):
        params = _migrate_params_v0_to_v1(params)

    return params



def change_case(case, series):
    if case == 'upper':
        return series.str.upper()
    elif case == 'lower':
        return series.str.lower()


def build_regex(type, char_cats, char_custom):
    # Keep spaces in all scenarios
    pattern_list = []
    if type == 'delete':
        if char_cats:
            for char in char_cats:
                pattern_list.append(f'[{char}]')
        if char_custom:
            for char in char_custom:
                pattern_list.append(f'[{char}]')
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
            escaped = ''.join([re.escape(c) for c in char_custom])
            pattern += f'(?![{escaped}])'
        pattern += r'[\d\D]'
        return re.compile(pattern, re.UNICODE)


# Get the unicode categories in scope per input parameters
def get_unicode_categories(char_params):
    category_types = [unicode_cat_map[key]
                      for key, value in char_params['categories'].items()
                      if value]
    return category_types if category_types else None


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

    columns = [c.strip() for c in params['colnames'].split(',')]
    space_params = {
        'type': params['type_space']
    }
    char_params = {
        'type': params['type_char'],
        'categories': {}
    }
    type_caps = params['type_caps']

    # Conditional Parameters
    if space_params['type'] != 'remove_all':
        space_params['condense'] = params['condense']
    else:
        space_params['condense'] = False

    for char_cat in unicode_cat_map.keys():
        if char_params['type'] != 'nop':
            char_params['categories'][char_cat] = params[char_cat]
        else:
            char_params['categories'][char_cat] = False

    char_params['char_cats'] = get_unicode_categories(char_params)
    if char_params['type'] != 'nop' and params['custom']:
        char_params['char_custom'] = set(params['chars'])
    else:
        char_params['char_custom'] = None

    # If not keep/drop params, skip
    if char_params['type'] != 'nop' and (char_params['char_cats'] or char_params['char_custom']):
        pattern = build_regex(char_params['type'], char_params['char_cats'],
                              char_params['char_custom'])
    else:
        pattern = None

    for column in columns:
        series = table[column]

        try:
            series.str
        except AttributeError:
            # Not a string column; skip it
            continue

        new_series = dispatch(space_params, type_caps, series, pattern)

        try:
            series.cat  # input was categorical; give categorical output
            new_series = new_series.astype('category')
        except AttributeError:
            # input was str, not categorical -- and so is new_series
            pass

        table[column] = new_series

    return table
