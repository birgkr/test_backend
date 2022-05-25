#!/usr/bin/env python3

import logging
import socket
import json

logger = logging.getLogger(__name__)


def upperKey(inParam):
    if type(inParam) is dict:
        return {k.upper():upperKey(v) for k,v in inParam.items()}
    elif type(inParam) is list:
        return [upperKey(i) for i in inParam]
    else:
        return inParam

def exactMatch(s):
    return f"^{s}$"

class CmdServer:
    def __init__(self):
        self.cmdUid = 1
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __del__(self):
        self.sock.close()

    def connect(self, address="localhost", port=8070):
        self.sock.connect((address, port))

    def sendCommand(self, jsonData):

        jsonData['UID'] = self.cmdUid
        self.cmdUid += 1

        # Send command
        msgStr = json.dumps(jsonData)
        msgBytes = msgStr.encode('utf-8')
        data = b'\xA5' + b'\xB1' + int.to_bytes(len(msgBytes), 4, 'big') + msgBytes 
        self.sock.sendall(data)

        # Read response
        rData = self.sock.recv(4096)
        return upperKey(json.loads(rData))


    def startTestServer(self, port=8090):
        jsonData = {'COMMAND': 'START_SERVER',
                    'COMMAND_DATA': { 'LPORT': port }  }
        resp = self.sendCommand(jsonData)
        return HttpServer(self, resp['COMMAND_DATA']['SERVER_ID'])


class HttpServer:
    def __init__(self, cmdSrv, id):
        self.cmdSrv = cmdSrv
        self.id = id

    def reset(self):
        jsonData = { 'COMMAND': 'RESET_SERVER',
                     'COMMAND_DATA': { 'SERVER_ID': self.id }  }
        resp = self.cmdSrv.sendCommand(jsonData)
    
    def kill(self):
        jsonData = { 'COMMAND': 'KILL_SERVER',
                     'COMMAND_DATA': { 'SERVER_ID': self.id }  }
        resp = self.cmdSrv.sendCommand(jsonData)

    def fetchStatus(self):
        jsonData = { 'COMMAND': 'FETCH_STATUS',
                     'COMMAND_DATA': { 'SERVER_ID': self.id }  }
        resp = self.cmdSrv.sendCommand(jsonData)
        return resp

    def checkStatus(self):
        allStatus = self.fetchStatus()['COMMAND_DATA']
        #print(json.dumps(allStatus, indent=2))

        msgLines = ['']
        for stat in allStatus:
            if 'UNMATCHED_RULES' in stat and stat['UNMATCHED_RULES']:
                msgLines.append( "Expected more request(s)...")
            if 'EXPECTED' in stat:
                if "REQUEST_INFO" in stat:
                    msgLines.append(f"Tried match the request '{stat['REQUEST_INFO']['METHOD']} {stat['REQUEST_INFO']['URI']}'...")
                for e in stat['EXPECTED']:
                    self.createExpectMessage(e, msgLines)
            msgLines.append("=====")
        
        return len(allStatus)==0, '\n'.join(msgLines)


    def createExpectMessage(self, sObj, msgLines, tab=0, tabSize=2):
        indent = " " * tabSize * tab
        if 'COLLECTION_TYPE' in sObj:
            if sObj['COLLECTION_TYPE'] == 'ALL_IN_ORDER':
                #msgLines.append(f"{indent}ALL_IN_ORDER")
                for c in sObj['COLLECTION']:
                    self.createExpectMessage(c, msgLines, tab+1, tabSize)
            elif sObj['COLLECTION_TYPE'] == 'ALL_IN_ANY_ORDER':
                #msgLines.append(f"{indent}ALL_IN_ANY_ORDER")
                self.createExpectMessage(sObj['COLLECTION'][0], msgLines, tab+1, tabSize)
                for c in sObj['COLLECTION'][1:]:
                    msgLines.append(f"{indent}== OR ==")
                    self.createExpectMessage(c, msgLines, tab+1, tabSize)
            else:
                raise Exception("Not implemented")
        else:        
            #print(sObj)
            for m in sObj['RULE']:
                msgLines.append(f"{indent}{m}")


    def expect(self, ruleOrCollection):
        jsonData = { 'COMMAND': 'ADD_RULE',
                    'COMMAND_DATA': { 'SERVER_ID': self.id, 'RULE': ruleOrCollection.toJson() }  }
        resp = self.cmdSrv.sendCommand(jsonData)


        
class Response:
    def __init__(self, respData="", statusCode=200):
        self.statusCode = statusCode
        self.respHeaders = {}
        self.respData = respData

    def toJson(self):
        retObj = {'CODE': self.statusCode}
        if self.respHeaders:
            retObj['HEADERS'] = self.respHeaders
        if self.respData:
            retObj['DATA'] = self.respData
        return retObj

    def code(self, code):
        self.statusCode = code
        return self

    def headers(self, headers):
        self.respHeaders = headers
        return self

    def data(self, data):
        self.respData = data
        return self


class Matcher:
    URL = "URL"
    METHOD = "METHOD"
    HEADER = "HEADER"
    DATA = "DATA"
    FILE_DATA = "FILE_DATA"

    def __init__(self, entity, matchValue):
        self.entity = entity
        self.matchValue = matchValue
        self.negate = False

    def toJson(self):
        return { 'TYPE': self.entity,
                 'VALUE': self.matchValue,
                 'NEGATE': self.negate
        }
    

class Rule:
    def __init__(self):
        self.matchers = []
        self.calledAtLeast = 1
        self.calledAtMost = 100000
        self.response = None

    def toJson(self):
        return {
            'TYPE': 'MATCHER',
            'MATCHERS': [m.toJson() for m in self.matchers],
            'CALLED_TIMES': {'AT_LEAST': self.calledAtLeast, 'AT_MOST': self.calledAtMost},
            'RESPONSE': self.response.toJson()
        }

    def matchTimes(self, t):
        self.calledAtLeast = t
        self.calledAtMost = t
        return self

    def matchAtLeast(self, t):
        self.calledAtLeast = t
        return self

    def matchAtMost(self, t):
        self.calledAtMost = t
        return self

    def matchTimesRange(self, t1, t2):
        self.calledAtLeast = t1
        self.calledAtMost = t2
        return self

    def method(self, method):
        m = Matcher(Matcher.METHOD, method)
        self.matchers.append(m)
        return self


    def url(self, url):
        m = Matcher(Matcher.URL, url)
        self.matchers.append(m)
        return self

    def header(self, headerKey, headerVal):
        m = Matcher(Matcher.HEADER, (headerKey, headerVal))
        self.matchers.append(m)
        return self

    def headers(self, headers):
        for k in headers:
            m = Matcher(Matcher.HEADER, (k,headers[k]))
            self.matchers.append(m)
        return self

    def data(self, data):
        m = Matcher(Matcher.DATA, data)
        self.matchers.append(m)
        return self

    def fileData(self, filePath):
        m = Matcher(Matcher.FILE_DATA, filePath)
        self.matchers.append(m)
        return self

    def respondWith(self, r):
        self.response = r
        return self


class Collection:
    ALL_IN_ORDER = "ALL_IN_ORDER"
    ALL_IN_ANY_ORDER = "ALL_IN_ANY_ORDER"
    ANY_NUMBER = "ANY_NUMBER"

    def __init__(self):
        self.type = Collection.ALL_IN_ORDER
        self.times = 1 
        self.anyNum = 1
        self.rules = []

    def toJson(self):
        jsonObj = {
            'TYPE': 'COLLECTION',
            'COLLECTION_TYPE': self.type,
            'CALLED_TIMES': self.times,
            'RULES': [ r.toJson() for r in self.rules]
            }

        if self.type == Collection.ANY_NUMBER:
            jsonObj['ANY_NUMBER'] = self.anyNum

        return jsonObj


    def expectAllInOrder(self):
        self.type = Collection.ALL_IN_ORDER
        return self

    def expectAllInAnyOrder(self):
        self.type = Collection.ALL_IN_ANY_ORDER
        return self

    def expectAnyNumber(self, num):
        self.type = Collection.ANY_NUMBER
        self.anyNum = num
        return self
    
    def addRule(self, rule):
        self.rules.append(rule)
        return self

   

if __name__ == "__main__":
    pass