import numpy as np


def format_dict(data, indent_level=0):
    indentstr = '    '
    indent = indentstr * indent_level
    formatted_str = "{\n"
    for key, value in data.items():
        formatted_str += f'{indent}{indentstr}"{key}": '
        if isinstance(value, dict):
            formatted_str += format_dict(value, indent_level + 1) + ',\n'
        elif isinstance(value, list):
            formatted_str += "[\n"
            for element in value:
                if isinstance(element, dict):
                    formatted_str += f'{indent}{indentstr*2}' + format_dict(element, indent_level + 2) + ',\n'
                else:
                    formatted_str += f'{indent}{indentstr*2}{repr(element)},\n'
            formatted_str = formatted_str.rstrip(",\n") + f'\n{indent}    ]\n'
        else:
            formatted_str += f'{repr(value)},\n'
    formatted_str = formatted_str.rstrip(",\n") + f'\n{indent}}}'
    return formatted_str


def dict_from_np_struct(data, dtype, decode='gbk'):
    result = {}
    for name in dtype.names:
        val = data[name][0]
        if isinstance(val, bytes):
            val = val.split(b'\x00')[0].decode(decode, errors='ignore')
        result[name] = val
    return result


def safe_decode(buf, encoding='gbk'):
    if isinstance(buf, bytes):
        return buf.split(b'\x00')[0].decode(encoding, errors='ignore')
    return buf


def concat_datasets(datasets, dim='time'):
    import xarray as xr
    valid = [ds for ds in datasets if ds is not None]
    if not valid:
        return None
    return xr.concat(valid, dim=dim)
