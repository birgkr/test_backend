# TODO list

1. Move matching type to separate .py that both testapi and rules import.
2. A number of entites that refer to URI is incorrectly named URL.
3. Add support for explicitly test parameters
4. Add support for using file contents as response data
5. Add support for https
6. Add thread safety for testserver
7. Remove the automatic uppercase generation of the keys in the json data since it messes up stuff. E.g. headers in the status info