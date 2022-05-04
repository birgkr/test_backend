#!/usr/bin/env python3

import sys
from os import path

sys.path.append('../src')

import testapi


import unittest

commandServer = None
httpServer = None

class TestCommandProt(unittest.TestCase):
    def setUp(self):
      httpServer.reset()

    def test_1(self):
      print("1")
      #self.backend.expect(Rule().url("").header("","").data("")).Times(AtLeast(3)).response(200, data="", headers=[])
      pass
        
    def test_2(self):
      print("2")
      #self.backend.expect(Rule().url("").header("","").data("")).Times(AtLeast(3)).response(200, data="", headers=[])
      pass

    def tearDown(self):
      stat = httpServer.fetchStatus()



if __name__ == "__main__":
  cmdSrv = testapi.CmdServer()
  cmdSrv.connect()
  httpServer = cmdSrv.startServer()
  unittest.main()
