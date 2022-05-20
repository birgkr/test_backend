#!/usr/bin/env python3


import logging
import sys
from os import path
import requests
import json

sys.path.append('../src')

import testapi
from testapi import Rule, Response, Collection


import unittest

commandServer = None
httpServer = None

class TestCommandProt(unittest.TestCase):
    def setUp(self):
      httpServer.reset()

    def NN_test_getHeaderTest(self):
      httpServer.expect(Rule().url("banan").method("GET").header(testapi.exact("apa"), "b.pa")
                              .matchTimes(1)
                              .respondWith(Response().code(200).data("Hello 1!")))
      r = requests.get(url = "http://localhost:8090/banan", headers = {"apa": "bepa"})

      self.assertTrue(*httpServer.checkStatus())


    def NN_test_2(self):
      httpServer.expect(Rule().url("apa")
                              .matchTimes(1)
                              .respondWith(Response().code(200).data("Hello!").headers({'apa': 'bepa', 'cepa':'depa'})))
      
      httpServer.expect(Rule().url("bepa")
                              .matchTimes(1)
                              .respondWith(Response().code(200).data("Hello!").headers({'apa': 'bepa', 'cepa':'depa'})))


      r = requests.get(url = "http://localhost:8090/apa", headers = {'apa': 'bepa', 'cepa':'depa'})
      r = requests.get(url = "http://localhost:8090/bepa", headers = {'apa': 'bepa', 'cepa':'depa'})


      self.assertTrue(*httpServer.checkStatus())

    def test_collection(self):
      col = Collection()
      col.expectAllInAnyOrder()
      col.addRule(Rule().url("apa")
                              .matchAtLeast(1).matchAtMost(2)
                              .respondWith(Response().code(200).data("Hello!").headers({'apa': 'bepa', 'cepa':'depa'})))
      col.addRule(Rule().url("bepa")
                              .matchTimes(1)
                              .respondWith(Response().code(200).data("Hello!").headers({'apa': 'bepa', 'cepa':'depa'})))
      col.addRule(Rule().url("depa")
                              .matchTimes(1)
                              .respondWith(Response().code(200).data("Hello!").headers({'apa': 'bepa', 'cepa':'depa'})))

      httpServer.expect(col)

      r = requests.get(url = "http://localhost:8090/apa", headers = {'apa': 'bepa', 'cepa':'depa'})
      r = requests.get(url = "http://localhost:8090/bepa", headers = {'apa': 'bepa', 'cepa':'depa'})
      r = requests.get(url = "http://localhost:8090/cepa", headers = {'apa': 'bepa', 'cepa':'depa'})
      r = requests.get(url = "http://localhost:8090/apa", headers = {'apa': 'bepa', 'cepa':'depa'})
      r = requests.get(url = "http://localhost:8090/apa", headers = {'apa': 'bepa', 'cepa':'depa'})
      r = requests.get(url = "http://localhost:8090/apa", headers = {'apa': 'bepa', 'cepa':'depa'})


      self.assertTrue(*httpServer.checkStatus())

    def tearDown(self):
      pass




if __name__ == "__main__":

  # configure logging
  logging.getLogger("requests").setLevel(logging.WARNING)
  logging.getLogger("urllib3").setLevel(logging.WARNING)
  logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)03d [%(levelname)s: %(threadName)s] %(filename)s:%(lineno)d > %(message)s', datefmt='%H:%M:%S',
                      handlers=[
                          logging.FileHandler(filename="tests.log", mode='w'),
                          logging.StreamHandler()
                      ])

  cmdSrv = testapi.CmdServer()
  cmdSrv.connect()
  httpServer = cmdSrv.startTestServer()
  unittest.main(exit=False)
  httpServer.kill()
  
