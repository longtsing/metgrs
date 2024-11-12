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
