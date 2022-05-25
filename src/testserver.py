#!/usr/bin/env python3

import logging
import http.server
import threading
import re
import json


import rules


logger = logging.getLogger(__name__)


class RequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.processRequest()

    def do_POST(self):
        self.processRequest()
                    
    def do_PUT(self):
        self.processRequest()
    
    def processRequest(self):
        logger.debug(f"Request: {self.command} {self.path} from {self.client_address[0]}")


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
        self.topRule.done = False
        self.topRule.rules.append(rule)

    def getStatus(self):
        logger.debug(f"Get status of server '{self.id}'")

        if not self.topRule.passed:
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
        #rs = RequestsStatus(request.command, request.path, [{'KEY':k, 'VALUE':v} for k,v in request.headers.items() ])
        
        expectStatus = ExpectStatus()
        expectStatus.setRequestInfo(request.command, request.path)
        expectStatus.setIsRoot(True)
   
        if self.topRule.done:
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
                    # TODO: read data and search
                    pass
                elif m.type == rules.Matcher.FILE_DATA:
                    # TODO: read file data and search
                    pass

            if not allMatch:
                logger.debug("Request does not match rule")
                expectStatus.addChild(es)
            else:
                # Rule is matching the request
                rule.times += 1

                if rule.times >= rule.calledAtLeast:
                    rule.passed = True

                if rule.times == rule.calledAtMost:
                    rule.done = True

                logger.debug("Request matches rule")
                logger.debug(f"   times: {rule.times}, at least: {rule.calledAtLeast}, at most: {rule.calledAtMost}")
                logger.debug(f"   passed: {rule.passed}, done: {rule.done}")

                # It shouldn't be possible to validate the rule more than 'calledAtMost' 
                # since it would be flagged as done and not validated against...
                # So, we don't test for that here
                return rule.response
                
                


        elif rule.type == rules.RequestRule.COLLECTION:
            if rule.collectionType == rules.RequestRule.ALL_IN_ORDER:
                # find first rule not yet validated
                rulesToTest = [r for r in rule.rules if not r.done]
                if len(rulesToTest)>0:
                    logger.debug("Testing rules in collection ALL_IN_ORDER")
                    for r in rulesToTest:
                        #r = rulesToTest[ri]
                        es = ExpectStatus()
                        es.setCollectionType(rule.collectionType)
                        resp = self.validateRule(request, r, es)
                        
                        if resp is None:
                            if r.passed:
                                # The tested rule did not validate, but it might be ok since it already tested ok... (typically with atLeast matching)
                                # Set it to done and continue testing with next rule in line
                                logger.debug(f"Tested rule did not validate, but might be ok since it already tested ok. Test next rule..")
                                #r.done = True
                            else:
                                # The tested rule shall validate, but did not...
                                expectStatus.addChild(es)
                                return None
                        else:
                            if len(rulesToTest) == 1:
                                # this was the last rule and it were validated ok, so copy the status to the collection
                                rule.passed = r.passed
                                rule.done = r.done
                            # rule validated, so pass on the response
                            return resp
                    return None
            
            if rule.collectionType == rules.RequestRule.ALL_IN_ANY_ORDER:
                es = ExpectStatus()
                es.setCollectionType(rule.collectionType)

                # fetch all rules that has not been met
                rulesToTest = [r for r in rule.rules if not r.done]
                if len(rulesToTest)>0:
                    logger.debug("Testing rules in collection ALL_IN_ANY_ORDER")

                for r in rulesToTest:
                    resp = self.validateRule(request, r, es)
                    if resp is not None:
                        if len(rulesToTest) == len([x for x in rulesToTest if x.passed]):
                            # all rules in sequence marked as passed so mark sequence passed as well
                            rule.passed = r.passed
                        if len(rulesToTest) == len([x for x in rulesToTest if x.done]):
                            # all rules in sequence marked as done so mark sequence done as well
                            rule.done = r.done
                        return resp
                # No rule in the collection rule tree matched the request
                expectStatus.addChild(es)
                return None

            if rule.collectionType == rules.RequestRule.ANY_NUM:
                pass

        return None    


if __name__ == "__main__":
    pass

