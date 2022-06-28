using System;
using System.IO;
using System.Net;
using System.Net.Http;
using Newtonsoft.Json.Linq;

using testapi;

namespace main
{


    class Program
    {

        static string Get(string uri)
        {
            HttpWebRequest request = (HttpWebRequest)WebRequest.Create(uri);
            request.AutomaticDecompression = DecompressionMethods.GZip | DecompressionMethods.Deflate;

            using(HttpWebResponse response = (HttpWebResponse)request.GetResponse())
            using(Stream stream = response.GetResponseStream())
            using(StreamReader reader = new StreamReader(stream))
            {
                return reader.ReadToEnd();
            }
        }


        static void Main(string[] args)
        {
            
            var cmd = new testapi.CommandClient();
            cmd.Connect();

            testapi.HttpServer httpSrv = cmd.StartTestServer();

            httpSrv.Reset();

            var col = new testapi.Collection();
            col.AddRule(new testapi.Rule()
                                    .Method("GET")
                                    .Url("ApanBapan")
                                    .MatchTimes(1)
                                    .RespondWith( new testapi.Response("apa").Code(200) )
                            );
            col.AddRule(new testapi.Rule()
                                    .Method("GET")
                                    .Url("CepanDepan")
                                    .MatchTimes(1)
                                    .RespondWith( new testapi.Response("apa").Code(200) )
                            );

            col.ExpectAnyNumber(1);
            httpSrv.Expect( col );


            try
            {
                Program.Get("http://localhost:8090/CepanDepan");
            }
            catch
            {                
            }
            try
            {
                Program.Get("http://localhost:8090/ApanBapan");
            }
            catch
            {                
            }
            


            string apa;
            httpSrv.CheckStatus(out apa);

            Console.WriteLine(apa);

            cmd.Disconnect();

            //var r = new testapi.Rule();
            //r.MatchTimes(2).MatchTimes(5);
        }
    }
}
