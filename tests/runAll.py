#!/usr/bin/env python3

import logging
import unittest
import sys

import testBasicRules
import testCollections

sys.path.append('../src')

import commandserver


if __name__ == "__main__":

  # configure logging
  logging.getLogger("requests").setLevel(logging.WARNING)
  logging.getLogger("urllib3").setLevel(logging.WARNING)
  logging.basicConfig(level=logging.WARNING, format='%(asctime)s.%(msecs)03d [%(levelname)s: %(threadName)s] %(filename)s:%(lineno)d > %(message)s', datefmt='%H:%M:%S',
                      handlers=[
                          logging.FileHandler(filename="tests.log", mode='w'),
                          logging.StreamHandler()
                      ])



  cmdSrv = commandserver.CommandServer()
  cmdSrv.start()

  suite = unittest.TestSuite()  
  suite.addTest( unittest.defaultTestLoader.loadTestsFromTestCase(testBasicRules.BasicTests) )
  suite.addTest( unittest.defaultTestLoader.loadTestsFromTestCase(testCollections.CollectionsTests) )

  runner = unittest.TextTestRunner()
  runner.run(suite)

  cmdSrv.stop()
  
