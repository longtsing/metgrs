def format_dict(data, indent_level=0):
    """
    手动格式化字典为字符串，支持处理包含子对象（如嵌套字典、列表等）的复杂结构，保证缩进正常。
    :param data: 要格式化的字典数据
    :param indent_level: 当前缩进级别，初始化为0，递归调用时会根据层级增加
    :return: 格式化后的字符串表示
    """
    indentstr='    '
    indent = indentstr* indent_level  # 根据缩进级别确定缩进空格
    formatted_str = "{\n"
    for key, value in data.items():
        if(key=='__datas__'):
            if(len(value)==0):
                continue
        formatted_str += f'{indent}{indentstr}"{key}": '
        if hasattr(value, '__dict__'):
            formatted_str += format_dict(dict(value.__dict__), indent_level + 1)+',\n'
        elif isinstance(value, list):
            # 如果值是列表，分别处理列表中的每个元素
            formatted_str += "[\n"
            for element in value:
                if hasattr(element, '__dict__'):
                    # 列表中的元素是字典，同样递归调用format_dict进行格式化，并增加缩进级别
                    formatted_str += f'{indent}{indentstr*2}'+format_dict(dict(element.__dict__), indent_level + 2) + ',\n'
                else:
                    # 列表中的非字典元素，直接转换为字符串并添加缩进
                    formatted_str += f'{indent}{indentstr*2}{repr(element)},\n'
            formatted_str = formatted_str.rstrip(",\n") + f'\n{indent}    ]\n'
        else:
            # 对于其他基本类型值，直接转换为字符串并添加缩进
            formatted_str += f'{repr(value)},\n'
    formatted_str = formatted_str.rstrip(",\n") + f'\n{indent}}}'
    return formatted_str

class originData():
    def __init__(self):
        self.__datas__=[]

    def __getitem__(self, key):
        if(isinstance(key, int)):
            return self.__datas__[key]
        else:
            return getattr(self, key)

    def __setitem__(self, key, value):
        if(isinstance(key, int)):
            self.__datas__[key]=value
        else:
            setattr(self, key, value)

    def append(self,value):
        self.__datas__.append(value)
    
    def __len__(self):
        return len(self.__datas__)

    def update(self, other):
        """
        更新当前originData实例，支持传入字典、originData实例、包含键值对元组的可迭代对象等进行更新。
        """
        if isinstance(other, dict):
            for key, value in other.items():
                self[key] = value
        elif isinstance(other, originData):
            for key in other:
                self[key] = other[key]
        elif hasattr(other, '__iter__'):  # 检查是否可迭代
            for element in other:
                if isinstance(element, tuple) and len(element) == 2:  # 检查是否为类似键值对的元组
                    key, value = element
                    self[key] = value

    def __str__(self):
        selfdict=dict(self.__dict__)
        if(self.__len__()==0):
            selfdict.pop('__datas__')
        return format_dict(selfdict)

    def __repr__(self):
        return self.__str__()

    @classmethod
    def from_dict(cls, input_dict):
        origin_obj = cls()
        for key, value in input_dict.items():
            origin_obj[key] = value
        return origin_obj