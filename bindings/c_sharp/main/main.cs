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

            testapi.HttpServer httpSrv = cmd.StartTestServer();
            
            httpSrv.Expect( new testapi.Rule()
                                    .Method("GET")
                                    .MatchTimes(2)
                                    .RespondWith( new testapi.Response("apa").Code(200) ) 
                          );

            cmd.Disconnect();

            //var r = new testapi.Rule();
            //r.MatchTimes(2).MatchTimes(5);
        }
    }
}
