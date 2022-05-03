#!/usr/bin/env python3

class Matcher:
    def __init__(self):
        self.type = None
        self.regExp = ""
        self.negate = False

class Response:
    def __init__(self):
        self.code = 200
        self.heders = []
        self.data = b''

class RequestRule:
    MATCHER = 0
    COLLECTION = 1

    ALL_IN_ORDER = 0
    ALL_IN_ANY_ORDER = 1
    ONE_OF = 2

    def __init__(self, jsonObj=None):
        self.type = None

    def __str__(self):
        return self.toStr(tab=0, indent=2)

    def toStr(self, tab, indent):
        if self.type == RequestRule.MATCHER:
            return "MATCHER"
        elif self.type == RequestRule.COLLECTION:
            return "COLLECTION"
        return "None"

    def addMatcher(self, matcher):
        if not self.matchers:
            self.matchers = [matcher]
        else:
            self.matchers.append(matcher)
        self.response = Response()

    def createCollection(self, collectionType=ALL_IN_ORDER):
        pass



if __name__ == "__main__":
    pass