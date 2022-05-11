#!/usr/bin/env python3

import logging
import http.server
import threading
import re

import rules


logger = logging.getLogger(__name__)


class RequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.processRequest()

    def do_POST(self):
        self.processRequest()
                    
    
    def processRequest(self):
        # Validate the request
        resp = self.server.owner.validateRequest(self)

        # Send the response
        self.send_response(resp.code)
        for k in resp.headers:
            self.send_header(k, resp.headers[k])
        self.end_headers()

        message = resp.data
        if type(message) is str:
            self.wfile.write(bytes(message, "utf8"))
        else:
            self.wfile.write(resp.data)
    

    def log_message(self, format, *args):
        logger.debug(f"Request: {self.command} {self.path} from {self.client_address[0]}")
    
       



class RequestsStatus:
    def __init__(self, method, uri, headers, data=None):
        self.allOk = True
        self.method = method
        self.uri =  uri
        self.headers = headers
        self.data = data
        self.neverReceived = False

        self.failedExpects = []

    def addFail(self, text):
        self.allOk = False
        self.failedExpects.append(text)



class TestServer:
    def __init__(self, serverId, port, ifAddr="0.0.0.0"):
        self.id = serverId
        self.port = port
        self.ifAddr = ifAddr
        self.server = None

        self.rules = [] # List of objects of type rules.RequestRule
        self.status = []


    def serverRun(self):
        self.server = http.server.HTTPServer((self.ifAddr, self.port), RequestHandler)
        self.server.allow_reuse_address = True
        self.server.owner = self
        logger.info(f"Starting test server at {self.ifAddr}, {self.port}")

        self.server.serve_forever()

    def start(self):
        #print("Start test server at port: {}".format(self.port))
        logger.debug(f"Starting test server thread...")
        self.srvThread = threading.Thread(target=TestServer.serverRun, name="T-TestServer", args=(self,))
        self.srvThread.start()


    def reset(self):
        logger.debug(f"Resetting test server '{self.id}'")

        self.rules = []
        self.status = []

    def stop(self):
        logger.debug(f"Stopping test server '{self.id}'")

        self.server.shutdown()
        self.server.server_close()
        self.srvThread.join()

    def addRule(self, rule):
        logger.debug(f"Adding rule to server '{self.id}'")
        self.rules.append(rule)

    def getStatus(self):
        logger.debug(f"Get status of server '{self.id}'")

        if len(self.rules)>0:

            for r in self.rules:
                rs = RequestsStatus('', '', {})
                rs.addFail(f"Expected request")
                rs.neverReceived = True
                self.status.append(rs)            
        
        stat = self.status
        return stat


    def validateRequest(self, request):
        #TODO: collections
        # Check if expecting any requests...

        rs = RequestsStatus(request.command, request.path, { k:v for k,v in request.headers.items() })

        if len(self.rules) == 0:
            rs.addFail("No request expected, but received one...")
            self.status.append( rs ) 
            return rules.Response(400)

        # We still expect requests, so validate this one...

        # Get the rule in question...
        r = self.rules[0]
        r.times -= 1

        if r.times < 1:
            self.rules.pop(0)

        if r.type == rules.RequestRule.MATCHER:
            allOk = True
            #TODO: add report info of the missing matches
            for m in r.matchers:
                if m.type == rules.Matcher.METHOD:
                    o = re.search(m.matchValue, request.command)
                    if not o:
                        allOk = False
                        rs.addFail(f"Expected command matching '{m.matchValue}', but got '{request.command}'...")

                elif m.type == rules.Matcher.URL:
                    o = re.search(m.matchValue, request.path)
                    if not o:
                        allOk = False
                        rs.addFail(f"Expected URI matching '{m.matchValue}', but got '{request.path}'...")

                elif m.type == rules.Matcher.HEADER:
                    matchFound = False
                    for k in request.headers:
                        o = re.search(m.matchValue[0], k)
                        if o:
                            p = re.search(m.matchValue[1], request.headers[k])
                            if p:
                                matchFound = True
                                break                            
                    if not matchFound:
                        allOk = False
                        rs.addFail(f"Expected a header key matching '{m.matchValue[0]}' with value matching '{m.matchValue[1]}', but found none...")

                elif m.type == rules.Matcher.DATA:
                    # TODO: read data and search
                    pass
            
            self.status.append( rs )            
            if allOk:
                return r.response
            else:
                return rules.Response(400)

    


if __name__ == "__main__":
    pass

