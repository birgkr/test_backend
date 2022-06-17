#!/usr/bin/env python3

# HTTP server that handles and validate incoming requests. 
# Instantiated by the command server.

import logging
import http.server
import threading
import re
#import json

import rules
logger = logging.getLogger(__name__)






class RequestHandler(http.server.BaseHTTPRequestHandler):
    """The handler for incoming HTTP requests. Passes the request to the handler's owner (TestServer) for validation.
       Whatever response received back from validation is returned back as response to the request."""

    def do_GET(self):
        self.processRequest()

    def do_HEAD(self):
        self.processRequest()

    def do_POST(self):
        self.processRequest()
                    
    def do_PUT(self):
        self.processRequest()

    def do_DELETE(self):
        self.processRequest()
    
    def processRequest(self):
        """Process any incoming request, and sends back a response."""

        logger.debug(f"Request: {self.command} {self.path} from {self.client_address[0]}")

        self.requestBody = None
        if self.command == "POST" or self.command == "PUT":
            if 'Content-Length' in self.headers:
                contentLen = int(self.headers.get('Content-Length'))
                self.requestBody = self.rfile.read(contentLen).decode('UTF-8')
            else:
                logger.warning("Received POST request without 'Content-Length' header")

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
        """Blank out any log messages from the http.server 'subsystem'"""
        #logger.debug(f"Request: {self.command} {self.path} from {self.client_address[0]}")
        pass
    
       

class ExpectStatus:
    def __init__(self):
        self.requestUri = ''
        self.requestMethod = ''

        self.isRoot = False
        self.isCollection = False
        self.collectionType = -1
        self.fails = []
        self.children = []
        self.unmatchedRules = False

    def toJson(self):
        if self.isRoot:
            esObj = { 'REQUEST_INFO': { 'URI': self.requestUri, 'METHOD': self.requestMethod } }
            #esObj['ALL_OK'] = (len(self.children) + len(self.fails) == 0)
            esObj['UNMATCHED_RULES'] = self.unmatchedRules

            if len(self.children)>0:
                esObj['EXPECTED'] = [ x.toJson() for x in self.children ]

            return esObj


        elif self.isCollection:
            typeStr = {}
            typeStr[rules.RequestRule.ALL_IN_ORDER] = "ALL_IN_ORDER"
            typeStr[rules.RequestRule.ALL_IN_ANY_ORDER] = "ALL_IN_ANY_ORDER"
            typeStr[rules.RequestRule.ANY_NUM] = "ANY_NUM"

            return { 
                     'COLLECTION_TYPE': typeStr[self.collectionType],
                     'COLLECTION': [ x.toJson() for x in self.children ]
                   }
        else:
            return { 'RULE': self.fails }

    def setRequestInfo(self, method, uri):
        self.requestUri = uri
        self.requestMethod = method

    def addChild(self, child):
        self.children.append(child)
        self.isCollection = True

    def addRuleFail(self, failStr):
        self.fails.append(failStr)

    def addExpectedRequestFail(self, failStr):
        self.neverReceived = True
        self.addRuleFail(failStr)

    def setIsRoot(self, isRoot):
        self.isRoot = isRoot

    def setCollectionType(self, collectionType):
        self.collectionType = collectionType
        self.isCollection = True


class TestServer:
    def __init__(self, serverId, port, ifAddr="0.0.0.0"):
        self.id = serverId
        self.port = port
        self.ifAddr = ifAddr
        self.server = None
        self.status = [] # List of validation status (one for each expectation rule plus one for each request that was received but not expected)

        self.topRule = rules.RequestRule()
        self.topRule.type = rules.RequestRule.COLLECTION
        self.topRule.collectionType = rules.RequestRule.ALL_IN_ORDER



    def serverRun(self):
        self.server = http.server.HTTPServer((self.ifAddr, self.port), RequestHandler)
        self.server.allow_reuse_address = True
        self.server.owner = self
        logger.info(f"Starting test server at {self.ifAddr}, {self.port}")
        self.server.serve_forever()


    def start(self):
        logger.debug(f"Starting test server thread...")
        self.srvThread = threading.Thread(target=TestServer.serverRun, name="T-TestServer", args=(self,))
        self.srvThread.start()


    def reset(self):
        logger.debug(f"Resetting test server '{self.id}'")
        self.topRule = rules.RequestRule()
        self.topRule.type = rules.RequestRule.COLLECTION
        self.topRule.collectionType = rules.RequestRule.ALL_IN_ORDER

        self.status = []

    def stop(self):
        logger.debug(f"Stopping test server '{self.id}'")

        self.server.shutdown()
        self.server.server_close()
        self.srvThread.join()

    def addRule(self, rule):
        logger.debug(f"Adding rule to server '{self.id}'")
        self.topRule.state = rules.RequestRule.NOT_IN_USE
        self.topRule.rules.append(rule)

    def getStatus(self):
        logger.debug(f"Get status of server '{self.id}'")

        if self.topRule.state < rules.RequestRule.PASSED:
            # the top rule is not validated ok, so we have unmet rules...
            #TODO: traverse all rules in the tree and report all expectations that wasn't met
            es = ExpectStatus()
            es.setIsRoot(True)
            es.addExpectedRequestFail("Expected request...")
            es.unmatchedRules = True
            self.status.append(es)            

        return [x.toJson() for x in self.status]

    def validateRequest(self, request):
        # First check if expecting any requests at all...
        expectStatus = ExpectStatus()
        expectStatus.setRequestInfo(request.command, request.path)
        expectStatus.setIsRoot(True)
   
        if self.topRule.state == rules.RequestRule.DONE:
            # Request receved, but no rules left to match...
            msg = "No request expected, but received one..."
            logger.debug(msg)
            es = ExpectStatus()
            es.addRuleFail(msg)
            expectStatus.addChild(es)
            self.status.append( expectStatus ) 
            #print(json.dumps(expectStatus.toJson(), indent=2))
            return rules.Response(400)

   
        resp = self.validateRule(request, self.topRule, expectStatus)
        #print(json.dumps(expectStatus.toJson(), indent=2))

        if resp is None:
            logger.debug("Failed to match request against any rule...")
            self.status.append( expectStatus ) 
            return rules.Response(400)
        return resp

        

    def validateRule(self, request, rule, expectStatus):
        if rule.type == rules.RequestRule.MATCHER:
            #logger.debug(f"Testing rule...\n{rule.toStr()}")
            
            es = ExpectStatus()

            allMatch = True

            # Check all matchers for this rule
            for m in rule.matchers:
                if m.type == rules.Matcher.METHOD:
                    o = re.search(m.matchValue, request.command)
                    if not o:
                        allMatch = False

                        msg = f"Expected command matching '{m.matchValue}', but got '{request.command}'..."
                        logger.debug(msg)
                        es.addRuleFail(msg)

                elif m.type == rules.Matcher.URL:
                    o = re.search(m.matchValue, request.path)
                    if not o:
                        allMatch = False
                        msg = f"Expected URI matching '{m.matchValue}', but got '{request.path}'..."
                        logger.debug(msg)
                        es.addRuleFail(msg)

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
                        allMatch = False
                        msg = f"Expected a header key matching '{m.matchValue[0]}' with value matching '{m.matchValue[1]}', but found none..."
                        logger.debug(msg)
                        es.addRuleFail(msg)

                elif m.type == rules.Matcher.DATA:
                    if request.command != "POST" and request.command != "PUT":
                        allMatch = False
                        msg = f"Rule to match data, but received request is a {request.command}..."
                        logger.debug(msg)
                        es.addRuleFail(msg)
                    else:
                        if request.requestBody is None:
                            allMatch = False
                            msg = f"Rule to match data, no data received..."
                            logger.debug(msg)
                            es.addRuleFail(msg)
                        else:
                            o = re.search(m.matchValue, request.requestBody)
                            if not o:
                                allMatch = False
                                maxLen = min(100, len(request.requestBody))
                                dataSuffix = ("..." if maxLen != len(request.requestBody) else "")
                                msg = f"Expected data to contain '{m.matchValue}', but got '{request.requestBody[:maxLen]}{dataSuffix}'"
                                logger.debug(msg)
                                es.addRuleFail(msg)                    
                elif m.type == rules.Matcher.FILE_DATA:
                    # TODO: read file data and search
                    pass

            if not allMatch:
                logger.debug("Request does not match rule")
                expectStatus.addChild(es)
            else:
                # Rule is matching the request
                rule.times += 1
                rule.state = rules.RequestRule.IN_USE

                if rule.times >= rule.calledAtLeast:
                    rule.state = rules.RequestRule.PASSED

                if rule.times == rule.calledAtMost:
                    rule.state = rules.RequestRule.DONE


                logger.debug("Request matches rule")
                logger.debug(f"   times: {rule.times}, at least: {rule.calledAtLeast}, at most: {rule.calledAtMost}")
                logger.debug(f"   state: {rule.state}")

                # It shouldn't be possible to validate the rule more than 'calledAtMost' 
                # since it would be flagged as done and not validated against...
                # So, we don't test for that here
                return rule.response
                
                


        elif rule.type == rules.RequestRule.COLLECTION:
            if rule.collectionType == rules.RequestRule.ALL_IN_ORDER:
                # find first rule not yet validated
                rulesToTest = [r for r in rule.rules if r.state < rules.RequestRule.DONE]
                if len(rulesToTest)>0:
                    logger.debug("Testing rules in collection ALL_IN_ORDER {}".format("(top rule)" if rule is self.topRule else ""))
                    for r in rulesToTest:
                        es = ExpectStatus()
                        es.setCollectionType(rule.collectionType)
                        resp = self.validateRule(request, r, es)
                        
                        if resp is None:
                            if r.state >= rules.RequestRule.PASSED:
                                # The tested rule did not validate, but it might be ok since it already tested ok... (typically with atLeast matching)
                                # Set it to done and continue testing with next rule in line
                                logger.debug(f"Tested rule did not validate, but might be ok since it already tested ok. Test next rule..")
                            else:
                                # The tested rule shall validate, but did not...
                                logger.debug("The tested was expected to validate, but did not...")
                                expectStatus.addChild(es)
                                return None
                        else:
                            if len(rulesToTest) == len([x for x in rulesToTest if x.state == rules.RequestRule.PASSED]):
                                # all rules in sequence marked as passed so mark sequence passed as well
                                rule.state = rules.RequestRule.PASSED
                            if len(rulesToTest) == len([x for x in rulesToTest if x.state == rules.RequestRule.DONE]):
                                # all rules in sequence marked as done so mark sequence done as well
                                rule.state = rules.RequestRule.DONE 

                            # rule validated, so pass on the response
                            return resp
                    return None
            
            if rule.collectionType == rules.RequestRule.ALL_IN_ANY_ORDER:
                es = ExpectStatus()
                es.setCollectionType(rule.collectionType)

                # fetch all rules that has not been met
                rulesToTest = [r for r in rule.rules if r.state < rules.RequestRule.DONE]
                if len(rulesToTest)>0:
                    logger.debug("Testing rules in collection ALL_IN_ANY_ORDER")

                for r in rulesToTest:
                    resp = self.validateRule(request, r, es)
                    if resp is not None:
                        if len(rulesToTest) == len([x for x in rulesToTest if x.state == rules.RequestRule.PASSED]):
                            # all rules in sequence marked as passed so mark sequence passed as well
                            rule.state = rules.RequestRule.PASSED
                        if len(rulesToTest) == len([x for x in rulesToTest if x.state == rules.RequestRule.DONE]):
                            # all rules in sequence marked as done so mark sequence done as well
                            rule.state = rules.RequestRule.DONE 
                        return resp
                # No rule in the collection rule tree matched the request
                expectStatus.addChild(es)
                return None

            if rule.collectionType == rules.RequestRule.ANY_NUM:
                es = ExpectStatus()
                es.setCollectionType(rule.collectionType)

                # fetch rules that is done
                rulesDone = [r for r in rule.rules if r.state == rules.RequestRule.DONE]
                # fetch all rules that has been successfully validated against
                rulesToTest = [r for r in rule.rules if r.state == rules.RequestRule.IN_USE or r.state == rules.RequestRule.PASSED]

                # Test if already started rules max out the collection max
                if len(rulesToTest) + len(rulesDone) < rule.maxNum:
                    # not maxed out so fetch all rules that are not done
                    rulesToTest = [r for r in rule.rules if r.state < rules.RequestRule.DONE]
                
                if len(rulesToTest)>0:
                    logger.debug(f"Testing rules in collection ANY_NUM, max: {rule.maxNum}, left: {len(rulesToTest)}")

                for r in rulesToTest:
                    resp = self.validateRule(request, r, es)
                    if resp is not None:
                        rule.times += 1
                        if len(rulesToTest) == len([x for x in rulesToTest if x.state == rules.RequestRule.PASSED]):
                            # all rules in sequence marked as passed so mark sequence passed as well
                            rule.state = rules.RequestRule.PASSED
                        if len(rulesToTest) == len([x for x in rulesToTest if x.state == rules.RequestRule.DONE]):
                            # all rules in sequence marked as done so mark sequence done as well
                            rule.state = rules.RequestRule.DONE 
                        return resp
                # No rule in the collection rule tree matched the request
                expectStatus.addChild(es)
                return None


        return None    


if __name__ == "__main__":
    pass

