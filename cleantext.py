# -*- coding: utf-8 -*-
import re

m_map = {
    'type_space':   'Trim around value|Trim before value|Trim after value|Remove all spaces|Leave as is'.lower().split('|'),
    'type_caps':    'Leave as is|Uppercase|Lowercase'.lower().split('|'),
    'type_char':    'Keep all|Drop|Keep'.lower().split('|')
}

# Map to set child params to Default if condition
c_map = {
    'type_space': 'remove all spaces',
    'type_char': 'keep all'
}

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
    'trim before value': r'^[\s]+',
    'trim after value': r'[\s]+$',
    'trim around value': r'^[\s]+|[\s]+$',
    'remove all spaces': r'[\s]'
}


def change_case(case, series):
    if case == 'uppercase':
        return series.str.upper()
    elif case == 'lowercase':
        return series.str.lower()


def build_regex(type, char_cats, char_custom):
    # Keep spaces in all scenarios
    pattern_list = []
    if type == 'drop':
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
    if space_params['type'] != 'leave as is':
        series = series.str.replace(space_regex_map[space_params['type']], '')
    if space_params['condense']:
        series = series.str.replace(r'[\s]+', ' ')
    if type_caps != 'leave as is':
        series = change_case(type_caps, series)
    return series


def render(table, params):
    # No processing if parameters define no change
    if not params['colnames'] or (
            params['type_space'] == m_map['type_space'].index('leave as is')
            and params['type_caps'] == m_map['type_caps'].index('leave as is')
            and params['type_char'] == m_map['type_char'].index('keep all')):
        return table

    columns = [c.strip() for c in params['colnames'].split(',')]
    space_params = {
        'type': m_map['type_space'][params['type_space']]
    }
    char_params = {
        'type': m_map['type_char'][params['type_char']],
        'categories': {}
    }
    type_caps = m_map['type_caps'][params['type_caps']]

    # Conditional Parameters
    if space_params['type'] != c_map['type_space']:
        space_params['condense'] = params['condense']
    else:
        space_params['condense'] = False

    for char_cat in unicode_cat_map.keys():
        if char_params['type'] != c_map['type_char']:
            char_params['categories'][char_cat] = params[char_cat]
        else:
            char_params['categories'][char_cat] = False

    char_params['char_cats'] = get_unicode_categories(char_params)
    char_params['char_custom'] = set(params['chars']) if (
            char_params['type'] != c_map['type_char'] and params['custom']
    ) else None

    # If not keep/drop params, skip
    if char_params['type'] != 'keep all' and (char_params['char_cats'] or char_params['char_custom']):
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
