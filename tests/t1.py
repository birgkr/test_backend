#!/usr/bin/env python3



import socketserver
from socket import MSG_DONTWAIT
import json

import socket

HOST = "localhost"
PORT = 8070  



def sendCommand(sock, jsonData) -> str:
    # Send command
    msgStr = json.dumps(jsonData)
    msgBytes = msgStr.encode('utf-8')
    data = b'\xA5' + b'\xB1' + int.to_bytes(len(msgBytes), 4, 'big') + msgBytes 
    sock.sendall(data)

    print('data sent')

    # Read response
    rData = sock.recv(4096)
    retObj = json.loads(rData)
    return json.dumps(retObj, indent=2)




with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    
    jsonData = { 'UID': 1,
                 'COMMAND': 'START_SERVER',
                 'COMMAND_DATA': { 'LPORT': 8080 }  }
    print(sendCommand(s, jsonData))


    jsonData = {  'UID': 2,
                  'COMMAND': 'ADD_RULE',
                  'COMMAND_DATA': 
                  { 
                    'SERVER_ID': 1,
                    'RULE': 
                    {
                        'TYPE': 'MATCHER',
                        'MATCHERS': 
                        [
                            { 
                              'TYPE': 'URL',
                              'REGEXP': 'apa',
                              'NEGATE': False
                            }
                        ]
                    }
                  }  
                }
    print(sendCommand(s, jsonData))



#import unittest
#
#class TestCommandProt(unittest.TestCase):
#    def setUp(self):
#        pass
#
#    def test_upper(self):
#        pass
#
#if __name__ == '__main__':
#    unittest.main()


