# -*- coding: utf-8 -*-

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
    'number':   '\d',
    'letter':   '^\W\d_',
    'punc':     '!-#%-*,-/:-;?-@[-\]_{}¡«·»¿;·՚-՟։-֊־׀׃׆׳-״؉-؊،-؍؛؞-؟٪-٭۔܀-܍߷-߹।-॥' \
                '॰෴๏๚-๛༄-༒༺-༽྅࿐-࿔၊-၏჻፡-፨᙭-᙮᚛-᚜᛫-᛭᜵-᜶។-៖៘-៚᠀-᠊᥄-᥅᧞-᧟᨞-᨟᭚-᭠᰻-᰿᱾-᱿\u2000-\u206e' \
                '⁽-⁾₍-₎〈-〉❨-❵⟅-⟆⟦-⟯⦃-⦘⧘-⧛⧼-⧽⳹-⳼⳾-⳿⸀-\u2e7e\u3000-〾゠・꘍-꘏꙳꙾꡴-꡷꣎-꣏꤮-꤯꥟꩜-꩟﴾-﴿︐-︙︰-﹒﹔' \
                '-﹡﹣﹨﹪-﹫！-＃％-＊，-／：-；？-＠［-］＿｛｝｟-･'
}

space_regex_map = {
    'trim before value':    '^[\s]+',
    'trim after value':     '[\s]+$',
    'trim around value':    '^[\s]+|[\s]+$',
    'remove all spaces':    '[\s]'
}

def change_case(type, table):
    if type == 'uppercase':
        return table.str.upper()
    elif type == 'lowercase':
        return table.str.lower()

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
        pattern = '(?!\s)'
        # To drop all else, set char regex in negative lookahead then drop all else [\d\D]
        if char_cats:
            for char in char_cats:
                pattern += f'(?![{char}])'
        if char_custom:
            for char in char_custom:
                pattern += f'(?![{"".join([re.escape(c) for c in char_custom])}])'
        pattern += f'[\d\D]'
        return re.compile(pattern, re.UNICODE)

# Get the unicode categories in scope per input parameters
def get_unicode_categories(char_params):
    category_types = [unicode_cat_map[key] for key, value in char_params['categories'].items() if value]
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
    space_params['condense'] = params['condense'] if space_params['type'] != c_map['type_space'] else False

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
        pattern = build_regex(char_params['type'], char_params['char_cats'], char_params['char_custom'])
    else:
        pattern = None


    for column in columns:
        # For now, re-categorize after replace. Can improve performance by operating
        # directly on categorical index, if needed
        if table[column].dtype.name == 'category':
            table[column] = prep_cat(table[column])
            table[column] = dispatch(space_params, type_caps, table[column].astype(str), pattern).astype('category')
        # Numbers need to cast as string
        elif np.issubdtype(table[column].dtype, np.number):
            table[column] = dispatch(space_params, type_caps, table[column].fillna('').astype(str), pattern)
        # Object
        else:
            table[column] = dispatch(space_params, type_caps, table[column], pattern)

    return table

def prep_cat(series):
    if '' not in series.cat.categories:
        series.cat.add_categories('', inplace=True)
    if any(series.isna()):
            series.fillna('', inplace=True)
    return series
