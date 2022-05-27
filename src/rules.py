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

    def toStr(self, tab=0, tabSize=2):
        indent = " " * tabSize * tab
        indent2 = indent + " " * tabSize
        ret = f"{indent}Status code: {self.code}\n"
        ret += f"{indent}- Headers -\n"
        for k in self.headers:
            ret += f"{indent2}{k}: {self.headers[k]}\n"
        ret += f"{indent2}-----\n"
        ret += f"{indent}Data: '{self.data}'\n"
        return ret


class RequestRule:
    NOT_IN_USE = 0  # Rule not tested ok
    IN_USE = 1      # Rule validated ok at least once (used with ANY_NUM collection)
    PASSED = 2      # Rule passed minimum criteria (e.g. match at least times, but not at most)
    DONE = 3        # Rule fully matched, will not be tested again

    MATCHER = 0
    COLLECTION = 1

    ALL_IN_ORDER = 0
    ALL_IN_ANY_ORDER = 1
    ANY_NUM = 2

    def __init__(self):
        self.type = None
        self.times = 0          # How many times this rule has been matched

        self.state = RequestRule.NOT_IN_USE

        # Collection specifics
        self.collectionType = None
        self.maxNum = 1
        self.rules = []

        # Matching specifics
        self.matchers = []
        self.calledAtLeast = 0
        self.calledAtMost = 0
        self.response = None


    def __str__(self):
        return self.toStr(tab=0, tabSize=2)

    def toStr(self, tab=0, tabSize=2):
        indent = " " * tabSize * tab
        indent2 = indent + " " * tabSize
        if self.type == RequestRule.MATCHER:
            retStr = f"{indent}== Rule ==\n"
            retStr += f"{indent}Called at least: {self.calledAtLeast}\n"
            retStr += f"{indent}Called at most: {self.calledAtMost}\n"
            retStr += f"{indent}Matchers...\n"
            for m in self.matchers:
                retStr += f"{indent2}{str(m)}\n"

            retStr += f"{indent}Response...\n"
            retStr += f"{indent}{self.response.toStr(tab+1, tabSize)}\n"
           
        elif self.type == RequestRule.COLLECTION:
            retStr = f"{indent}== Collection ==\n"
            typeStrs = ['ALL_IN_ORDER', 'ALL_IN_ANY_ORDER', 'ANY_NUM']
            retStr += f"{indent}Collection type: {typeStrs[self.collectionType]}\n"
            retStr += f"{indent}Times: {self.times}\n"
            if self.collectionType == RequestRule.ANY_NUM:
                retStr += f"{indent}Max num: {self.maxNum}\n"
            for r in self.rules:
                retStr += f"{indent}{r.toStr(tab+1, tabSize)}\n"
            
        return retStr

    def addMatcher(self, matcher):
        self.matchers.append(matcher)

    def createCollection(self, collectionType=ALL_IN_ORDER):
        pass

    def setResponse(self, r):
        self.response = r



if __name__ == "__main__":
    pass