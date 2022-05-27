#!/usr/bin/env python3

# The test backend is composed of two main parts.
# 1. A controllable http(s) web server
# 2. A command server that handles the command channel from/to the test framework


#TODO: Add logging

import logging
import socketserver
import json

import testserver
import rules
import testapi


logger = logging.getLogger(__name__)

nextServerId = 1
testServers = {}


class TransportPDU:
    def __init__(self, request):
        self.MAGIC_BYTES = 0xA5B1
        
        self.magic = int.from_bytes(request.recv(2), 'big')
        self.dataSize = int.from_bytes(request.recv(4), 'big')
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
        d = {k.upper():v for k,v in self.__dict__.items()}
        return json.dumps(self.__dict__, default=lambda x: {k.upper():v for k,v in x.__dict__.items()}).encode('utf-8')


class CommandRequestHandler(socketserver.BaseRequestHandler):
    """Request handles for all incoming control commands."""

    def handle(self):
        """Called when a new chunk of TCP data has been received. Does some validation, parse the data and send a response back to the client."""
        
        # Fetch and execute all incomming commands
        magic = self.request.recv(1)
        while len(magic) == 1:
            if magic != b'\xA5':
                logger.warning(f"Invalid magic in protocol...")
            #TODO validate protocol version               
            versionId = self.request.recv(1)
            dataSize = int.from_bytes(self.request.recv(4), 'big')
            #TODO: Sanity check of data size 
            msgData = self.request.recv(dataSize)
            
            #TODO: Handle ill formed data (eg. non JSON)
            cmdObj = json.loads(msgData)
            # Parse the command
            retObj = self.parseCmd(cmdObj)
            

            logger.debug(f"Send response for command {cmdObj['COMMAND']}...")
            # Send back command status
            #TODO: Use message structure (magic, dataSize, ...)
            self.request.sendall(retObj.toJsonStr())
            
            # Check for next msg
            try:
                magic = self.request.recv(1)
            except:
                break



    def parseCmd(self, cmd):
        """Parses the command data"""
        
        # Initialise base return status message
        retObj = CmdRetStatus(code=CmdRetStatus.STAT_INVALID_CMD, text='Unknown command: {}'.format(cmd['COMMAND']))

        logger.debug(f"Received command: {cmd['COMMAND']}")

        # Execute the incomming command
        if cmd['COMMAND'].upper() == "START_SERVER":
            retObj = self.cmdStartServer(cmd['COMMAND_DATA'])
        elif cmd['COMMAND'].upper() == "RESET_SERVER":
            retObj = self.cmdResetServer(cmd['COMMAND_DATA'])
        elif cmd['COMMAND'].upper() == "KILL_SERVER":
            retObj = self.cmdKillServer(cmd['COMMAND_DATA'])
        elif cmd['COMMAND'].upper() == "ADD_RULE":
            retObj = self.cmdAddServerRule(cmd['COMMAND_DATA'])
        elif cmd['COMMAND'].upper() == "FETCH_STATUS":
            retObj = self.cmdFetchStatus(cmd['COMMAND_DATA'])
        
        retObj.uid = cmd['UID']
        retObj.cmd = cmd['COMMAND']
        return retObj
        

    def cmdStartServer(self, cmdData):
        lPort = cmdData['LPORT']
        
        global nextServerId
        global testServers

        logger.debug(f"Starting test server with id '{nextServerId}' at port '{lPort}'")
        newServer = testserver.TestServer(nextServerId, lPort)
        testServers[nextServerId] = newServer
        nextServerId += 1
        newServer.start()

        retObj = CmdRetStatus(code=CmdRetStatus.STAT_SUCCESS, text='Started server, id: {}'.format(newServer.id))
        retObj.command_data = { 'SERVER_ID':newServer.id }
        return retObj

    def cmdResetServer(self, cmdData):
        serverId = cmdData['SERVER_ID']
        global testServers

        logger.debug(f"Resetting server with id '{serverId}'")
        testServers[serverId].reset()
        return CmdRetStatus(code=CmdRetStatus.STAT_SUCCESS, text='Server reset')

    def cmdKillServer(self, cmdData):
        serverId = cmdData['SERVER_ID']
        global testServers

        logger.debug(f"Stopping server with id '{serverId}'")
        testServers.pop(serverId).stop()
        
        return CmdRetStatus(code=CmdRetStatus.STAT_SUCCESS, text='Server killed')

    def cmdAddServerRule(self, cmdData):
        serverId = cmdData['SERVER_ID']

        logger.debug(f"Adding rule to server with id '{serverId}'")
        rule = self.ruleFromJson(cmdData['RULE'])

        #print(json.dumps(cmdData,indent=2))
        #print(str(rule))

        global testServers
        testServers[serverId].addRule(rule)
        return CmdRetStatus(code=CmdRetStatus.STAT_SUCCESS, text='Added rule')

    def cmdFetchStatus(self, cmdData):
        serverId = cmdData['SERVER_ID']

        logger.debug(f"Fetch status for server with id '{serverId}'")
        stat = testServers[serverId].getStatus()
        retObj = CmdRetStatus(code=CmdRetStatus.STAT_SUCCESS, text='Fetch status')
        retObj.command_data = stat
        return retObj


    def ruleFromJson(self, ruleData):
        rule = rules.RequestRule()

        #print(json.dumps(ruleData, indent=2))

        #TODO: Validate the rule itself? E.g. can't expect data in a GET request... maybe enough with warning on client-side?

        if ruleData['TYPE'] == 'MATCHER':
            rule.type = rules.RequestRule.MATCHER
            for m in ruleData['MATCHERS']:
                rule.addMatcher(self.matcherFromJson(m))
            if 'CALLED_TIMES' in ruleData:
                rule.calledAtLeast, rule.calledAtMost = self.timesFromJson(ruleData['CALLED_TIMES'])
                if rule.calledAtLeast == 0:
                    rule.passed = True
            if 'RESPONSE' in ruleData:
                rule.setResponse(self.responseFromJson(ruleData['RESPONSE']))

        elif ruleData['TYPE'] == 'COLLECTION':
            rule.type = rules.RequestRule.COLLECTION
            rule.collectionType = self.collectionTypeFromJson(ruleData['COLLECTION_TYPE'])
            rule.times = ruleData['CALLED_TIMES']
            if rule.collectionType == rules.RequestRule.ANY_NUM:
                rule.maxNum = ruleData['MAX_NUMBER']
            
            for r in ruleData['RULES']:
                rule.rules.append(self.ruleFromJson(r))

        return rule

    def matcherFromJson(self, mData):
        matcher = rules.Matcher()

        matcher.type = mData['TYPE']
        matcher.matchValue = mData['VALUE']
        matcher.negate = mData['NEGATE']

        return matcher


    def timesFromJson(self, tData):
        return (tData['AT_LEAST'], tData['AT_MOST'])
       

    def responseFromJson(self, rData):
        resp = rules.Response()
        resp.code = int(rData['CODE'])
        if 'HEADERS' in rData:
            resp.headers = rData['HEADERS']
        if 'DATA' in rData:
            resp.data = rData['DATA']
        return resp

    def collectionTypeFromJson(self, data):
        if data == "ALL_IN_ORDER":
            return rules.RequestRule.ALL_IN_ORDER
        elif data == "ALL_IN_ANY_ORDER":
            return rules.RequestRule.ALL_IN_ANY_ORDER
        elif data == "ANY_NUMBER":
            return rules.RequestRule.ANY_NUM
        else:
            return None

class CommandServer():
    """The CommandServer handles all controls commands sent from the client-side test framework."""
    
    def __init__(self, host="0.0.0.0", port=8070):
        """Creates and starts a command server."""
        logger.info(f"Starting command server at '{host}:{port}'")
        socketserver.TCPServer.allow_reuse_address = True
        self.srv = socketserver.TCPServer((host, port), CommandRequestHandler)
        self.srv.serve_forever()

if __name__ == "__main__":
    # configure logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)03d [%(levelname)s: %(threadName)s] %(filename)s:%(lineno)d > %(message)s', datefmt='%H:%M:%S',
                        handlers=[
                            logging.FileHandler(filename="tests.log", mode='w'),
                            logging.StreamHandler()
                        ])
        
    
    cmdSrv = CommandServer()
    #httpSrv = 

    #cmd = commands.CmdStartServer()
    #print(cmd.__dict__)
    #print(isinstance(cmd, commands.CmdStartServer))
    
    