# Command Protocol

## General
When started the server listens for incomming TCP connections and then (control) commands. E.g. to start a test backend or set the behaviour of an alredy started one etc.
The strucure of the data is a command in JSON format wrapped in a simlpe transport protocol. 

The transport is structured as 1 magic byte (0xA5) followed by a 1 byte version identifier, 4 byte indicating the size of the json data and then the json data itself.
Currently the version indicator is 0xB0 + version number. All values are big endian (aka network order).
Eg. Sending "{}" would result in the stream [A5 B1 02 00 00 00 7b 7d]


## Commands
All command are in JSON and consist of a common part and a part that is dependent on the issued command.
All received commands results in a response message with the result of the command. The responses are in JSON and wrapped in the same transport as the commands.

### Common structure

#### General command
```
{
    'UID': 'integer unique id of the command message',
    'COMMAND': 'the command as a string',
    'COMMAND_DATA': { 'command specific data' }
}
```
The UID identifier is any integer the command issuer see fit, it will be returned in the response as a link to the command.

#### General response
```
{
    'UID': 'the UID of the corresponding command message',
    'COMMAND': 'the issued command',
    'CODE': 'integer/enum status code of the command result',
    'TEXT': 'string representation of the result (typically the error message upon failure)',
    'COMMAND_DATA': { 'command specific response data' }
}
```



### The commands
Listing the COMMAND_DATA section only...

#### Start server
```

Command
{
    'LPORT': integer listening port
    'PROTOCOL': either 'HTTP' or 'HTTPS'
    #TODO: add https support    
}

Response
{
    'SERVER_ID': integer server id
}
```



#### Reset server

#### Kill server

#### Add rule

```
{
    'SERVER_ID': id of the server
    
    'RULE': 
    {
        'TYPE': either 'COLLECTION' or 'MATCHER',
        # MATCHERS field is only present if type is MATCHER
        'MATCHERS': [],
        # 'COLLECTION' and 'COLLECTION_TYPE' fields are only present if TYPE is COLLECTION
        'COLLECTION_TYPE': one of (ALL_IN_ORDER, ALL_ANY_ORDER, ONE_OF),
        'COLLECTION': [ (type RULE) ]
    }
}
```





