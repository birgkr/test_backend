using System;
using testapi;
using Newtonsoft.Json.Linq;

namespace main
{
    class Program
    {
        static void Main(string[] args)
        {
            var cmd = new testapi.CommandClient();
            cmd.Connect();

            cmd.StartTestServer();
        
            cmd.Disconnect();
        }
    }
}
