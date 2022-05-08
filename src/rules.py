#!/usr/bin/env python3

class Matcher:
    URL = "URL"
    METHOD = "METHOD"
    HEADER = "HEADER"
    DATA = "DATA"
    FILE_DATA = "FILE_DATA"
    
    def __init__(self):
        self.type = None
        self.matchValue = None
        self.negate = False

    def __str__(self):
        return "{}: {}'{}'".format(self.type, "not matching " if self.negate else "", self.matchValue)

class Response:
    def __init__(self, code=200, headers=[], data=b''):
        self.code = code
        self.headers = headers
        self.data = data

    def __str__(self):
        ret = f"Status code: {self.code}\n"
        ret += "- Headers -\n"
        for k in self.headers:
            ret += f"{k}: {self.headers[k]}\n"
        ret += "-----\n"
        ret += f"Data: '{self.data}'\n"
        return ret


class RequestRule:
    MATCHER = 0
    COLLECTION = 1

    ALL_IN_ORDER = 0
    ALL_IN_ANY_ORDER = 1
    ONE_OF = 2

    def __init__(self):
        self.type = None
        self.matchers = []
        self.times = 0
        self.response = None

    def __str__(self):
        return self.toStr(tab=0, tabSize=2)

    def toStr(self, tab, tabSize):
        indent = " " * tabSize * tab
        indent2 = indent + " " * tabSize
        if self.type == RequestRule.MATCHER:
            retStr = f"{indent}Matchers...\n"
            for m in self.matchers:
                retStr += f"{indent2}{str(m)}\n"

            retStr += f"{indent}Response...\n"
            retStr += f"{indent2}{str(self.response)}\n"
            
            return retStr
        elif self.type == RequestRule.COLLECTION:
            return "COLLECTION"
        return "None"

    def addMatcher(self, matcher):
        self.matchers.append(matcher)

    def createCollection(self, collectionType=ALL_IN_ORDER):
        pass

    def setResponse(self, r):
        self.response = r



if __name__ == "__main__":
    pass