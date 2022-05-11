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

def exact(s):
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


    def startServer(self, port=8090):
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

        allOk = True
        msg = "\n"
        for stat in allStatus:
            if not stat['ALLOK']:
                allOk = False
                if stat['NEVERRECEIVED']:
                    msg += f"Expected request...\n"
                else:
                    msg += f"For the request '{stat['METHOD']} {stat['URI']}'\n"
                    for e in stat['FAILEDEXPECTS']:
                        msg += "  " + e + "\n"
                    msg += "\n"

        return allOk, msg


    def expect(self, rule):
        jsonData = { 'COMMAND': 'ADD_RULE',
                     'COMMAND_DATA': { 'SERVER_ID': self.id, 'RULE': rule.toJson() }  }
        resp = self.cmdSrv.sendCommand(jsonData)
        



class Response:
    def __init__(self):
        self.statusCode = 200
        self.respHeaders = None
        self.respData = None

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
        self.callTimes = 1
        self.response = None

    def toJson(self):
        return {
            'TYPE': 'MATCHER',
            'MATCHERS': [m.toJson() for m in self.matchers],
            'TIMES': self.callTimes,
            'RESPONSE': self.response.toJson()
        }


    def times(self, t):
        self.callTimes = t
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

    def respondWith(self, r):
        self.response = r
        return self

   

if __name__ == "__main__":
    pass