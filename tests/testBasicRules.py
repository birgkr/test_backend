#!/usr/bin/env python3


import logging
import sys
from os import path
import requests
import json

sys.path.append('../src')

import testapi
from testapi import Rule, Response


import unittest

#httpServer = None

class BasicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
      cls.cmdClient = testapi.CommandClient()
      cls.cmdClient.connect()
      cls.httpServer = cls.cmdClient.startTestServer()
    
    @classmethod
    def tearDownClass(cls):
      cls.httpServer.kill()
      cls.cmdClient.disconnect()

    def setUp(self):
      self.httpServer.reset()


    def test_getTestPos(self):
      """Validate GET request"""
      self.httpServer.expect(Rule().method("GET")
                              .matchTimes(1)
                              .respondWith(Response()))
      r = requests.get(url = "http://127.0.0.1:8090/banan")

      self.assertTrue(*self.httpServer.checkStatus())


    def test_getTestNeg(self):
      """Expect GET request, but sending a POST... shall fail"""
      self.httpServer.expect(Rule().method("GET")
                              .matchTimes(1)
                              .respondWith(Response()))
      r = requests.post(url = "http://127.0.0.1:8090/banan")

      self.assertFalse(*self.httpServer.checkStatus())


    def test_postTestPos(self):
      """Validate GET request"""
      self.httpServer.expect(Rule().method("POST").data("apan bapan").header("Content-Length","10")
                              .matchTimes(1)
                              .respondWith(Response()))
      r = requests.post(url = "http://127.0.0.1:8090/banan", data="apan bapan")

      self.assertTrue(*self.httpServer.checkStatus())



    def test_matchTimesPos(self):
      """Validate exact matching times"""
      self.httpServer.expect(Rule().method("GET")
                              .matchTimes(3)
                              .respondWith(Response()))
      r = requests.get(url = "http://127.0.0.1:8090/banan")
      r = requests.get(url = "http://127.0.0.1:8090/jhljkh")
      r = requests.get(url = "http://127.0.0.1:8090/ljkah")

      self.assertTrue(*self.httpServer.checkStatus())

    def test_matchTimesNeg_toFew(self):
      """Validate exact matching times, but to few requests"""
      self.httpServer.expect(Rule().method("GET")
                              .matchTimes(4)
                              .respondWith(Response()))
      r = requests.get(url = "http://127.0.0.1:8090/")
      r = requests.get(url = "http://127.0.0.1:8090/wewwed")
      r = requests.get(url = "http://127.0.0.1:8090/gfhd")

      #self.assertTrue(*httpServer.checkStatus())
      stat, msgs = self.httpServer.checkStatus()
      self.assertFalse(stat)
      self.assertTrue("Expected more request" in "".join(msgs), "Incorrect error message")


    def test_matchTimesNeg_toMany(self):
      """Validate exact matching times, but to many requests"""
      self.httpServer.expect(Rule().method("GET")
                              .matchTimes(2)
                              .respondWith(Response()))
      r = requests.get(url = "http://127.0.0.1:8090/")
      r = requests.get(url = "http://127.0.0.1:8090/wewwed")
      r = requests.get(url = "http://127.0.0.1:8090/gfhd")

      stat, msgs = self.httpServer.checkStatus()
      self.assertFalse(stat)
      self.assertTrue("No request expected, but" in "".join(msgs), "Incorrect error message")



    def test_matchAtLeastPos(self):
      """Validate at least matching times"""
      self.httpServer.expect(Rule().method("GET").url("apa")
                              .matchAtLeast(3)
                              .respondWith(Response()))
      r = requests.get(url = "http://127.0.0.1:8090/apa")
      r = requests.get(url = "http://127.0.0.1:8090/jhlapajkh")
      r = requests.get(url = "http://127.0.0.1:8090/apaljkah")


      self.httpServer.expect(Rule().method("GET").url("bepa")
                              .matchAtLeast(2)
                              .respondWith(Response()))
      r = requests.get(url = "http://127.0.0.1:8090/bepa")
      r = requests.get(url = "http://127.0.0.1:8090/jhljkhbepa")
      r = requests.get(url = "http://127.0.0.1:8090/bepaljkah")

      self.assertTrue(*self.httpServer.checkStatus())


    def test_matchAtLeastNeg(self):
      """Validate at least matching times, to few requests"""
      self.httpServer.expect(Rule().method("GET")
                              .matchAtLeast(3)
                              .respondWith(Response()))
      r = requests.get(url = "http://127.0.0.1:8090/banan")
      r = requests.get(url = "http://127.0.0.1:8090/jhljkh")

      stat, msgs = self.httpServer.checkStatus()
      self.assertFalse(stat)
      self.assertTrue("Expected more request" in "".join(msgs), "Incorrect error message")


    def test_matchAtMostPos(self):
      """Validate at most matching times"""
      self.httpServer.expect(Rule().method("GET")
                              .matchAtMost(3)
                              .respondWith(Response()))
      r = requests.get(url = "http://127.0.0.1:8090/apa")
      r = requests.get(url = "http://127.0.0.1:8090/apa")
      r = requests.get(url = "http://127.0.0.1:8090/apa")

      self.httpServer.expect(Rule().method("GET")
                              .matchAtMost(4)
                              .respondWith(Response()))
      r = requests.get(url = "http://127.0.0.1:8090/bepa")
      r = requests.get(url = "http://127.0.0.1:8090/bepa")
      r = requests.get(url = "http://127.0.0.1:8090/bepa")

      self.assertTrue(*self.httpServer.checkStatus())


    def test_matchAtMostNeg(self):
      """Validate at most matching times, but too many"""
      self.httpServer.expect(Rule().method("GET")
                              .matchAtMost(2)
                              .respondWith(Response()))
      r = requests.get(url = "http://127.0.0.1:8090/banan")
      r = requests.get(url = "http://127.0.0.1:8090/jhljkh")
      r = requests.get(url = "http://127.0.0.1:8090/ljkah")

      stat, msgs = self.httpServer.checkStatus()
      self.assertFalse(stat)
      self.assertTrue("No request expected, but" in "".join(msgs), "Incorrect error message")



if __name__ == "__main__":

  # configure logging
  logging.getLogger("requests").setLevel(logging.WARNING)
  logging.getLogger("urllib3").setLevel(logging.WARNING)
  logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)03d [%(levelname)s: %(threadName)s] %(filename)s:%(lineno)d > %(message)s', datefmt='%H:%M:%S',
                      handlers=[
                          logging.FileHandler(filename="tests.log", mode='w'),
                          logging.StreamHandler()
                      ])

  unittest.main(exit=False)
  
