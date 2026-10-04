class Conflict(ValueError):
    def __init__(self,index,code):
        self.index=index;self.code=code;super().__init__(code)
