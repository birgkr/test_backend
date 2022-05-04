#!/usr/bin/env python3

import socket
import json

def upperKey(inParam):
    if type(inParam) is dict:
        return {k.upper():upperKey(v) for k,v in inParam.items()}
    elif type(inParam) is list:
        return [upperKey(i) for i in inParam]
    else:
        return inParam


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
    
    def fetchStatus(self):
        return ""


class Response:
    def __init__(self):
        self.code = 200
        self.headers = []
        self.data = ""

class Matcher:
    def __init__(self):
        pass

class Rule:
    def __init__(self):
        self.matchers = []

class Expectation:
    def __init__(self):
        self.response = Response()

    def times(t):
        return self
        


class TestServer:
    def __init__(self):
        pass

    def expect(self, rule: Rule) -> Expectation:
        e = Expectation()
        return e

    def collection(self):
        pass


if __name__ == "__main__":
    pass