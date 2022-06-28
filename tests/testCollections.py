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

httpServer = None

class CollectionsTests(unittest.TestCase):

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

    def test_collectionInOrderPos(self):
      col = Collection()
      col.addRule(Rule().url("apa")
                              .matchTimes(2)
                              .respondWith(Response().code(200).data("Hello!")))
      col.addRule(Rule().url("bepa")
                              .matchTimes(1)
                              .respondWith(Response().code(200).data("Hello!")))

      self.httpServer.expect(col)

      r = requests.get(url = "http://127.0.0.1:8090/apa")
      r = requests.get(url = "http://127.0.0.1:8090/apa")
      r = requests.get(url = "http://127.0.0.1:8090/bepa")
      self.assertTrue( self.httpServer.checkStatus())


    def test_collectionAnyOrderPos(self):
      col = Collection()
      col.expectAllInAnyOrder()
      col.addRule(Rule().url("apa")
                              .matchAtLeast(1).matchAtMost(2)
                              .respondWith(Response().code(200).data("Hello!")))
      col.addRule(Rule().url("bepa")
                              .matchTimes(1)
                              .respondWith(Response().code(200).data("Hello!")))
      col.addRule(Rule().url("cepa")
                              .matchTimes(2)
                              .respondWith(Response().code(200).data("Hello!")))

      self.httpServer.expect(col)

      r = requests.get(url = "http://127.0.0.1:8090/apa")
      r = requests.get(url = "http://127.0.0.1:8090/cepa")
      r = requests.get(url = "http://127.0.0.1:8090/bepa")
      r = requests.get(url = "http://127.0.0.1:8090/cepa")
      r = requests.get(url = "http://127.0.0.1:8090/apa")

      self.assertTrue( self.httpServer.checkStatus())


    def test_collectionAnyOrderNeg(self):
      col = Collection()
      col.expectAllInAnyOrder()
      col.addRule(Rule().url("apa")
                              .matchAtLeast(1).matchAtMost(2)
                              .respondWith(Response().code(200).data("Hello!")))
      col.addRule(Rule().url("bepa")
                              .matchTimes(1)
                              .respondWith(Response().code(200).data("Hello!")))
      col.addRule(Rule().url("cepa")
                              .matchTimes(2)
                              .respondWith(Response().code(200).data("Hello!")))

      self.httpServer.expect(col)

      r = requests.get(url = "http://127.0.0.1:8090/apa")
      r = requests.get(url = "http://127.0.0.1:8090/cepa")
      r = requests.get(url = "http://127.0.0.1:8090/bepa")
      r = requests.get(url = "http://127.0.0.1:8090/apa")

      stat, msgs = self.httpServer.checkStatus()
      self.assertFalse(stat)
      self.assertTrue("Expected more request" in "".join(msgs), "Incorrect error message")



    def test_collectionAnyNumPos(self):
      col = Collection()
      col.expectAnyNumber(2)
      col.addRule(Rule().url("apa")
                              .matchAtLeast(1).matchAtMost(2)
                              .respondWith(Response().code(200).data("Hello!")))
      col.addRule(Rule().url("bepa")
                              .matchTimes(1)
                              .respondWith(Response().code(200).data("Hello!")))
      col.addRule(Rule().url("cepa")
                              .matchTimes(2)
                              .respondWith(Response().code(200).data("Hello!")))

      self.httpServer.expect(col)

      r = requests.get(url = "http://127.0.0.1:8090/apa")
      r = requests.get(url = "http://127.0.0.1:8090/cepa")
      r = requests.get(url = "http://127.0.0.1:8090/cepa")
      r = requests.get(url = "http://127.0.0.1:8090/apa")

      self.assertTrue( self.httpServer.checkStatus())



    def test_collectionAnyNumNeg(self):
      col = Collection()
      col.expectAnyNumber(2)
      col.addRule(Rule().url("apa")
                              .matchAtLeast(1).matchAtMost(2)
                              .respondWith(Response().code(200).data("Hello!")))
      col.addRule(Rule().url("bepa")
                              .matchTimes(1)
                              .respondWith(Response().code(200).data("Hello!")))
      col.addRule(Rule().url("cepa")
                              .matchTimes(2)
                              .respondWith(Response().code(200).data("Hello!")))

      self.httpServer.expect(col)

      r = requests.get(url = "http://127.0.0.1:8090/apa")
      r = requests.get(url = "http://127.0.0.1:8090/cepa")
      r = requests.get(url = "http://127.0.0.1:8090/bepa")
      r = requests.get(url = "http://127.0.0.1:8090/apa")

      stat, msgs = self.httpServer.checkStatus()

      self.assertFalse(stat)
      self.assertTrue("Expected URI matching" in "".join(msgs), "Incorrect error message")


    def test_collectionAnyNumNeg2(self):
      col = Collection()
      col.expectAnyNumber(1)
      col.addRule(Rule().url("apa")
                              .matchTimes(1)
                              .respondWith(Response().code(200).data("Hello!")))
      col.addRule(Rule().url("bepa")
                              .matchTimes(1)
                              .respondWith(Response().code(200).data("Hello!")))

      self.httpServer.expect(col)

      r = requests.get(url = "http://127.0.0.1:8090/bepa")
      r = requests.get(url = "http://127.0.0.1:8090/apa")

      stat, msgs = self.httpServer.checkStatus()
      
      self.assertFalse(stat)
      self.assertTrue("No request expected" in "".join(msgs), "Incorrect error message")



    def test_nestedCollectionPos(self):
      colTop = Collection()
      col1 = Collection()
      col1.expectAllInAnyOrder()
      col2 = Collection()
      col2.expectAllInAnyOrder()

      col1.addRule(Rule().url("c1_1")
                              .matchTimes(1)
                              .respondWith(Response().code(200).data("Hello!")))
      col1.addRule(Rule().url("c1_2")
                              .matchTimes(1)
                              .respondWith(Response().code(200).data("Hello!")))

      col2.addRule(Rule().url("c2_1")
                              .matchTimes(1)
                              .respondWith(Response().code(200).data("Hello!")))
      col2.addRule(Rule().url("c2_2")
                              .matchTimes(1)
                              .respondWith(Response().code(200).data("Hello!")))

      colTop.addRule(col1)
      colTop.addRule(col2)

      self.httpServer.expect(colTop)

      r = requests.get(url = "http://127.0.0.1:8090/c1_2")
      r = requests.get(url = "http://127.0.0.1:8090/c1_1")
      r = requests.get(url = "http://127.0.0.1:8090/c2_2")
      r = requests.get(url = "http://127.0.0.1:8090/c2_1")
      self.assertTrue( self.httpServer.checkStatus())




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
  
