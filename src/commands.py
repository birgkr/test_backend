#!/bin/usr/env python3


class CommandMsg:
    def __init__(self):
        self.uid = 0
        self.command = ""

    def fromJson(self, jsonObj):
        self.uid = jsonObj['UID']
        self.command = jsonObj['COMMAND']


class CommandRetStatus:
    def __init__(self):
        self.uid = 0
        self.command = ""
        self.code = 0
        self.text = ""

    def toJson(self):
        return {
            'UID': self.uid,
            'COMMAND': self.command,
            
        }



class CmdStartServer(CommandMsg):
    def __init__(self):
        super().__init__()
        self.lport = 80

    def fromJson(self, jsonObj):
        super().fromJson(jsonObj)
        self.lport = jsonObj['LPORT']



class CmdStartServerStatus(CommandRetStatus):
    def __init__(self):
        super().__init__()
        self.serverId = 0

"""
{
    'UID': 2,
    'COMMAND': 'SOME_COMMAND'
    'COMMAND_DATA': 
    {
        'MAIN_DATA': 'some data'
    }
}
"""

class CommandMarchaller:
    def __init__(self):
        pass

    def toJson(self, cmdMsg):

        jsonObj = { 'UID': cmdMsg.uid, 'COMMAND': cmdMsg.command }

        if isinstance(cmdMsg, CmdStartServer):
            jsonObj['COMMAND_DATA'] = { 'LPORT': cmdMsg.lport }

        return ""

    def fromJson(self, jsonObj) -> CommandMsg:
        return None
