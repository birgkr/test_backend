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


    def test_1(self):
      httpServer.expect(Rule().method("GET").url("apa")
                              .respondWith(Response()))

      r = requests.get(url = "http://127.0.0.1:8090/bepa")

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

  cmdClient = testapi.CommandClient()
  cmdClient.connect()
  httpServer = cmdClient.startTestServer()
  unittest.main(exit=False)
  httpServer.kill()
  
