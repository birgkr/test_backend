#!/usr/bin/env python3

import sys
from os import path
import requests
import json

sys.path.append('../src')

import testapi
from testapi import Rule, Response


import unittest

commandServer = None
httpServer = None

class TestCommandProt(unittest.TestCase):
    def setUp(self):
      httpServer.reset()

    def test_1(self):
      httpServer.expect(Rule().url("banan").method("GET").header(testapi.exact("apa"), "bepa")
                              .times(1)
                              .respondWith(Response().code(200).data("Hello 1!")))

      r = requests.get(url = "http://localhost:8090/banan", headers = {"apa": "bepa"})

      self.assertTrue(*httpServer.checkStatus())


    def test_2(self):
      httpServer.expect(Rule().url("apa")
                              .times(1)
                              .respondWith(Response().code(200).data("Hello!").headers({'apa': 'bepa', 'cepa':'depa'})))
      
      httpServer.expect(Rule().url("apa2")
                              .times(1)
                              .respondWith(Response().code(200).data("Hello!").headers({'apa': 'bepa', 'cepa':'depa'})))


      r = requests.get(url = "http://localhost:8090/apa", headers = {'apa': 'bepa', 'cepa':'depa'})
      r = requests.get(url = "http://localhost:8090/apa2", headers = {'apa': 'bepa', 'cepa':'depa'})


      self.assertTrue(*httpServer.checkStatus())

    def tearDown(self):
      pass




if __name__ == "__main__":
  cmdSrv = testapi.CmdServer()
  cmdSrv.connect()
  httpServer = cmdSrv.startServer()
  unittest.main(exit=False)
  httpServer.kill()
  
