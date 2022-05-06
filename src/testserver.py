#!/usr/bin/env python3

import http.server
import threading
import rules


class RequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        resp = self.server.owner.rules[0].response



        print("GET request: {}".format(self.path))
        print("Headers...")
        for k in self.headers:
            print("  {} = {}".format(k,self.headers[k]))

        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        message = resp.data
        self.wfile.write(bytes(message, "utf8"))

class TestServer:
    def __init__(self, serverId, port, ifAddr="0.0.0.0"):
        self.id = serverId
        self.port = port
        self.ifAddr = ifAddr
        self.server = None

        self.rules = [] # List of objects of type rules.RequestRule


    def serverRun(self):
        self.server = http.server.HTTPServer((self.ifAddr, self.port), RequestHandler)
        self.server.allow_reuse_address = True
        self.server.owner = self
        self.server.serve_forever()

    def start(self):
        print("Start test server at port: {}".format(self.port))
        self.srvThread = threading.Thread(target=TestServer.serverRun, args=(self,))
        self.srvThread.start()

    def reset(self):
        self.rules = []

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.srvThread.join()

    def addRule(self, rule):
        self.rules.append(rule)

if __name__ == "__main__":
    pass

