import regex
import numpy as np

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

# Define characters by unicode category:
# https://www.unicode.org/reports/tr44/#General_Category_Values
# Broad category 1 char, specific 2 char
unicode_cat_map = {
    'number': 'N',
    'letter': 'L',
    'punc': 'P'
}

def clean_space(type, string):
    if type == 'trim around value':
        return string.strip()
    elif type == 'trim before value':
        return string.lstrip()
    elif type == 'trim after value':
        return string.rstrip()
    else:
        # Remove all separator and control characters
        return regex.sub(regex.compile(r'\p{Zs}|\p{C}'), '', string)

def condense_space(string):
    # To not overwrite strip selection,
    # preserve leading & trailing spaces
    value = regex.sub('^[ \t]+|[ \t]+$', '', string)
    return string.replace(value, ' '.join(string.split()))

def change_case(type, string):
    if type == 'uppercase':
        return string.upper()
    elif type == 'lowercase':
        return string.lower()

def build_regex(type, char_cats, char_custom):
    pattern = '[^\p{Zs}\p{C}' if type == 'keep' else '['
    if char_cats:
        for cat in char_cats:
            pattern += f'\p{{{cat}}}'
    if char_custom:
        pattern += ''.join([regex.escape(c) for c in char_custom])
    pattern += ']'
    return regex.compile(pattern)

# Get the unicode categories in scope per input parameters
def get_unicode_categories(char_params):
    category_types = [unicode_cat_map[key] for key, value in char_params['categories'].items() if value]
    return category_types if category_types else None

def dispatch(space_params, type_caps, string, pattern=None):
    if pattern:
        string = regex.sub(pattern, '', string)
    if space_params['type'] != 'leave as is':
        string = clean_space(space_params['type'], string)
    if space_params['condense']:
            string = condense_space(string)
    if type_caps != 'leave as is':
        string = change_case(type_caps, string)
    return string

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
        dispatcher = lambda x: dispatch(space_params, type_caps, x, pattern) if x else None
    else:
        dispatcher = lambda x: dispatch(space_params, type_caps, x) if x else None

    dtypes = table[columns].get_dtype_counts().index

    for dtype in dtypes:
        # For now, re-categorize after replace. Can improve performance by operating
        # directly on categorical index
        dtype_columns = table[columns].dtypes[table[columns].dtypes == dtype].index
        if dtype == 'category':
            # categorical string cast will cast None as text `nan'. Need to fill first
            for col in dtype_columns:
                if '' not in table[col].cat.categories:
                    table[col].cat.add_categories('', inplace=True)
                table[col].fillna('', inplace=True)
                table[col] = table[col].astype(str).map(dispatcher).astype('category')
        # Numbers need to cast as string
        elif np.issubdtype(dtype, np.number):
            table[dtype_columns] = table[dtype_columns].astype(str).applymap(dispatcher)
        # Object
        else:
            table[dtype_columns] = table[dtype_columns].applymap(dispatcher)

    return table



