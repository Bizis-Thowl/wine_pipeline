import re

def anchor_parser(condition_str):
    # Pattern for variable like "x1", "volatile acidity", "sugar level", etc.
    var_pattern = r'[a-zA-Z\s]+'
    # Pattern for numbers, which may be integers or floats
    num_pattern = r'-?\d+(\.\d+)?'
    # Full pattern that includes an optional second number and takes into account the variable being before or after the number
    full_pattern = fr'(({var_pattern})\s*(<=|<|=|>=|>)\s*({num_pattern})\s*(and\s*(<=|<|=|>=|>)\s*({num_pattern})?)?)|(({num_pattern})\s*(<=|<|=|>=|>)\s*({var_pattern})\s*(and\s*(<=|<|=|>=|>)\s*({num_pattern})?)?)'

    match = re.fullmatch(full_pattern, condition_str.strip())
    if not match:
        raise ValueError(f'Invalid condition string: {condition_str}')
    
    lb = None
    ub = None

    groups = match.groups()
    if groups[1] is not None:  # var first case
        value = groups[1].strip()
        if groups[2] in ('<=', '<'):
            ub = float(groups[3])
        elif groups[2] in ('>=', '>'):
            lb = float(groups[3])

        if groups[5] is not None:  # 2nd condition exists
            if groups[5] in ('<=', '<'):
                ub = float(groups[6])
            elif groups[5] in ('>=', '>'):
                lb = float(groups[6])
    else:  # num first case
        value = groups[9].strip()
        if groups[8] in ('<=', '<'):
            lb = float(groups[7])
        elif groups[8] in ('>=', '>'):
            ub = float(groups[7])

        if groups[11] is not None:  # 2nd condition exists
            if groups[11] in ('<=', '<'):
                lb = float(groups[12])
            elif groups[11] in ('>=', '>'):
                ub = float(groups[12])

    return {'value': value, 'upper_bound': ub, 'lower_bound': lb}
