#!/usr/bin/env python3

import sys
from os import path

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
      #httpServer.expect(Rule().url("").header("","").data("").times(2))
      pass

    def test_2(self):
      httpServer.expect(Rule().url("").header("","").data("")
                              .times(2)
                              .respondWith(Response().code(200).data("").headers([('apa', 'bepa'), ('cepa','depa')])))
      

    def tearDown(self):
      stat = httpServer.fetchStatus()



if __name__ == "__main__":
  cmdSrv = testapi.CmdServer()
  cmdSrv.connect()
  httpServer = cmdSrv.startServer()
  unittest.main()
