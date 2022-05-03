#!/usr/bin/env python3

# The test backend is composed of two main parts.
# 1. A controllable http(s) web server
# 2. A command server that handles the command channel from/to the test framework


#TODO: Add logging

from socket import MSG_DONTWAIT
import socketserver
import json

import commands
import testserver
import rules


nextServerId = 1
testServers = {}


class TransportPDU:
    def __init__(self, request):
        self.MAGIC_BYTES = 0xA5B1
        
        self.magic = int.from_bytes(request.recv(2), 'little')
        self.dataSize = int.from_bytes(request.recv(4), 'little')
        self.data = request.recv(self.dataSize)

        self.cmdObj = json.loads(self.data)

    def __str__(self):
        return "== {:04x}/{} ==\n{}".format(self.magic, self.dataSize, self.data.decode('utf-8'))



    def getData(self) -> dict:
        """Get message data as json object"""
        return None

class CmdRetStatus:
    STAT_SUCCESS = 0
    STAT_ERROR = 1
    STAT_INVALID_CMD = 2
    STAT_NOT_IMPLEMENTED = 3

    def __init__(self, uid=0, cmd='', code=STAT_ERROR, text='Unknown error'):
        self.uid = uid
        self.cmd = cmd
        self.code = code
        self.text = text

    def toJsonStr(self):
        return json.dumps({'UID': self.uid, 
         'COMMAND': self.cmd, 
         'CODE': self.code, 
         'TEXT': self.text }).encode('utf-8')


class CommandRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):

        # Fetch and execute all incomming commands
        magic = self.request.recv(1)
        while len(magic) == 1:
            if magic != b'\xA5':
                print("Invalid magic!")
            #TODO validate protocol version               
            versionId = self.request.recv(1)
            dataSize = int.from_bytes(self.request.recv(4), 'big')
            #TODO: Sanity check of data size 
            msgData = self.request.recv(dataSize)
            
            #TODO: Handle ill formed data (eg. non JSON)
            cmdObj = json.loads(msgData)

            # Parse the command
            retObj = self.parseCmd(cmdObj)
            # Send back command status
            #TODO: Use message structure (magic, dataSize, ...)
            self.request.sendall(retObj.toJsonStr())
            
            # Check for next msg
            try:
                magic = self.request.recv(1)
            except:
                break

        #print('Done')


    def parseCmd(self, cmd):
        # Initialise base return status message
        retObj = CmdRetStatus(code=CmdRetStatus.STAT_INVALID_CMD, text='Unknown command: {}'.format(cmd['COMMAND']))

        print(f"Incoming command: {cmd['COMMAND'].upper()}")

        # Execute the incomming command
        if cmd['COMMAND'].upper() == "START_SERVER":
            retObj = self.cmdStartServer(cmd['COMMAND_DATA'])
        elif cmd['COMMAND'].upper() == "ADD_RULE":
            retObj = self.cmdAddServerRule(cmd['COMMAND_DATA'])
        
        retObj.uid = cmd['UID']
        retObj.cmd = cmd['COMMAND']
        return retObj
        

    def cmdStartServer(self, cmdData):
        lPort = cmdData['LPORT']
        
        global nextServerId
        global testServers

        newServer = testserver.TestServer(nextServerId, lPort)
        testServers[nextServerId] = newServer
        nextServerId += 1
        newServer.start()

        return CmdRetStatus(code=CmdRetStatus.STAT_SUCCESS, text='Started server, id: {}'.format(newServer.id))

    def cmdResetServer(self, cmdData):
        serverId = cmdData['SERVER_ID']
        pass

    def cmdRemoveServer(self, cmdData):
        pass

    def cmdAddServerRule(self, cmdData):
        serverId = cmdData['SERVER_ID']
        rule = rules.RequestRule(cmdData['RULE'])

        global testServers
        testServers[serverId].addRule(rule)

        print(rule)
        return CmdRetStatus(code=CmdRetStatus.STAT_SUCCESS, text='Added rule')




class CommandServer():
    def __init__(self, host="localhost", port=8070):
        socketserver.TCPServer.allow_reuse_address = True
        self.srv = socketserver.TCPServer(("0.0.0.0", port), CommandRequestHandler)
        self.srv.serve_forever()

if __name__ == "__main__":
    cmdSrv = CommandServer()
    #httpSrv = 

    #cmd = commands.CmdStartServer()
    #print(cmd.__dict__)
    #print(isinstance(cmd, commands.CmdStartServer))
    
    