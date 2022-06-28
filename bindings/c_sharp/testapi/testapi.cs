using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Collections.Generic;

using Newtonsoft.Json;
using Newtonsoft.Json.Linq;


namespace testapi
{
    public class CommandClient
    {
        private uint m_uid = 1;
        private string m_host = "";
        private int m_hostPort = 0;
        private TcpClient m_client;
        private NetworkStream m_sockStream;

        public bool Connect(string host="localhost", int port=8070)
        {          
            Console.WriteLine("Connect");

            try
            {            
                m_client = new TcpClient(host, port);
                m_sockStream = m_client.GetStream();
            }
            catch (Exception e)
            {
                Console.WriteLine(e.ToString());
                return false;
            }

            m_host = host;
            m_hostPort = port;


            return true;
        }

        public void Disconnect(bool killHttpServers=true)
        {
            if (killHttpServers)
            {
                JObject jObj = new JObject();
                SendCommand("KILL_ALL_SERVERS", jObj);                
            }
            

            Console.WriteLine("Disconnect");
            m_sockStream.Close();
            m_client.Close();
        }

        public HttpServer StartTestServer(int port=8090)
        {
            var jObj = new JObject();
            jObj.Add(new JProperty("LPORT", port));
            var resp = SendCommand("START_SERVER", jObj);           

            return new HttpServer(this, (int)resp.SelectToken("COMMAND_DATA.SERVER_ID"));
        }

        public JObject SendCommand(string command, JObject commandData)
        {
            JObject jObj = new JObject();
            jObj.Add(new JProperty("UID", m_uid));
            m_uid++;
            jObj.Add(new JProperty("COMMAND", command));
            jObj.Add(new JProperty("COMMAND_DATA", commandData));

            string jsonStr = jObj.ToString();


            byte[] jsonData = Encoding.UTF8.GetBytes(jsonStr);
            byte[] headerData = { 0xA5, 0xB1 };
            byte[] lengthData = BitConverter.GetBytes(jsonData.Length);
            if (BitConverter.IsLittleEndian)
                Array.Reverse(lengthData);

            m_sockStream.Write(headerData, 0, headerData.Length);
            m_sockStream.Write(lengthData, 0, lengthData.Length);
            m_sockStream.Write(jsonData, 0, jsonData.Length);

            byte[] bytes = new byte[4096];
            int bytesRead = m_sockStream.Read(bytes, 0, bytes.Length);

            jsonStr = Encoding.UTF8.GetString(bytes);

            JObject resp = JObject.Parse(jsonStr);

            //Console.WriteLine(resp["COMMAND_DATA"]["SERVER_ID"]);
            //Console.WriteLine(resp.SelectToken("COMMAND_DATA.SERVER_ID"));
            //Console.WriteLine(resp);

            return resp;

        }

    }



    public class HttpServer
    {
        protected CommandClient m_owner;
        protected int m_id;

        public HttpServer(CommandClient owner, int id)
        {
            m_owner = owner;
            m_id = id;
        }

        ~HttpServer()
        {
            Kill();
        }


        public void Reset()
        {
            JObject jObj = new JObject();
            jObj.Add(new JProperty("SERVER_ID", m_id));
            m_owner.SendCommand("RESET_SERVER", jObj);
        }

        public void Kill()
        {
            JObject jObj = new JObject();
            jObj.Add(new JProperty("SERVER_ID", m_id));
            m_owner.SendCommand("KILL_SERVER", jObj);
        }

        public JObject FetchStatus()
        {
            JObject jObj = new JObject();
            jObj.Add(new JProperty("SERVER_ID", m_id));
            return m_owner.SendCommand("FETCH_STATUS", jObj);
        }

        public bool CheckStatus(out string msg)
        {
            var jObj = FetchStatus();
            var allStatus = jObj["COMMAND_DATA"];

            //Console.WriteLine(allStatus.ToString());

            List<string> msgLines = new List<string>();
            foreach (var stat in allStatus)
            {

                var elem = stat.ToObject<JObject>();
                if (elem.ContainsKey("UNMATCHED_RULES") && (bool)elem.SelectToken("UNMATCHED_RULES"))
                {
                    msgLines.Add("Expected more request(s)...");
                }

                if (elem.ContainsKey("EXPECTED"))
                {
                    if (elem.ContainsKey("REQUEST_INFO"))
                    {
                        var reqInfo = elem["REQUEST_INFO"].ToObject<JObject>();
                        msgLines.Add($"Tried match the request '{reqInfo["METHOD"]} {reqInfo["URI"]}'...");
                    }

                    foreach(var e in stat["EXPECTED"])
                    {
                        var expectObj = e.ToObject<JObject>();
                        CreateExpectMessage(expectObj, msgLines);
                    }
                }
                msgLines.Add("=====");
            }


            msg = String.Join("\n", msgLines);

            return false;
        }

        protected void CreateExpectMessage(JObject obj, List<string> msgLines, int tab=0, int tabSize=2)
        {
            string indent = new string(' ', tab * tabSize);
            
            if (obj.ContainsKey("COLLECTION_TYPE"))
            {
                // Collection...
                string colType = (string)obj["COLLECTION_TYPE"];
                if (colType == "ALL_IN_ORDER")
                {
                    foreach (var c in obj["COLLECTION"])
                    {
                        CreateExpectMessage(c.ToObject<JObject>(), msgLines, tab+1, tabSize);
                    }

                }
                else if (colType == "ALL_IN_ANY_ORDER")
                {
                    msgLines.Add($"{indent}== ALL_IN_ANY_ORDER collection ==");
                    var arr = (JArray)obj["COLLECTION"];
                    CreateExpectMessage(arr[0].ToObject<JObject>(), msgLines, tab+1, tabSize);
                    for(var i=1; i<arr.Count; ++i)
                    {
                        msgLines.Add($"{indent}== OR ==");
                        CreateExpectMessage(arr[i].ToObject<JObject>(), msgLines, tab+1, tabSize);
                    }
                }
                else if (colType == "ANY_NUM")
                {
                    msgLines.Add($"{indent}== ANY_NUM collection ==");
                    var arr = (JArray)obj["COLLECTION"];
                    CreateExpectMessage(arr[0].ToObject<JObject>(), msgLines, tab+1, tabSize);
                    for(var i=1; i<arr.Count; ++i)
                    {
                        msgLines.Add($"{indent}== OR ==");
                        CreateExpectMessage(arr[i].ToObject<JObject>(), msgLines, tab+1, tabSize);
                    }
                }
            }
            else
            {
                // Rule(s)
                foreach(var m in obj["RULE"])
                {
                    msgLines.Add($"{indent}{(string)m}");
                }
            }
        }

        public void Expect(ExpectBase eb)
        {
            var jObj = new JObject();
            jObj.Add(new JProperty("SERVER_ID", m_id));
            jObj.Add(new JProperty("RULE", eb.ToJson()));            
            m_owner.SendCommand("ADD_RULE", jObj);
        }


    }


    public class Response
    {
        protected int m_statusCode;
        protected Dictionary<string, string>  m_respHeaders; 
        protected string m_respData;


        public Response(string respData="", int statusCode=200)
        {
            m_statusCode = statusCode;
            m_respHeaders = new Dictionary<string, string>();
            m_respData = respData;
        }

        public JObject ToJson()
        {
            var jObj = new JObject();
            jObj.Add(new JProperty("CODE", m_statusCode));
            jObj.Add(new JProperty("HEADERS", JObject.FromObject(m_respHeaders)));
            jObj.Add(new JProperty("DATA", m_respData));
            return jObj;        
        }        

        public Response Code(int statusCode)
        {
            m_statusCode = statusCode;
            return this;            
        }

        public Response Headers(Dictionary<string, string> headers)
        {
            m_respHeaders = headers;
            return this;            
        }

        public Response Data(string respData)
        {
            m_respData = respData;
            return this;            
        }
    }


    public class Matcher
    {
        public enum MatchType { URL, METHOD, HEADER, DATA, FILE_DATA };
        
        protected MatchType m_matchType;
        protected string m_matchValue1;
        protected string m_matchValue2; // So far, only used with header matching since it is key/value matching
        protected bool m_negate = false;

        public Matcher(MatchType mt, string matchValue, string matchValue2="")
        {
            m_matchType = mt;
            m_matchValue1 = matchValue;
            m_matchValue2 = matchValue2;
        }

        public JObject ToJson()
        {
            var jObj = new JObject();
            jObj.Add(new JProperty("TYPE", m_matchType.ToString()));

            if (m_matchType != MatchType.HEADER)
            {
                jObj.Add(new JProperty("VALUE", m_matchValue1));
            }
            else
            {
                var hArr = new JArray();
                hArr.Add(m_matchValue1);
                hArr.Add(m_matchValue2);
                jObj.Add(new JProperty("VALUE", hArr));
            }

            jObj.Add(new JProperty("NEGATE", m_negate));
            return jObj;        
        }        
    }

    public abstract class ExpectBase
    {
        protected enum BaseType { NONE, RULE, COLLECTION };
        protected BaseType baseType;

        public abstract JObject ToJson();
    }

    public class Rule : ExpectBase
    {
        protected List<Matcher> m_matchers = new List<Matcher>(); 
        protected int m_calledAtLeast = 1;
        protected int m_calledAtMost = 100000;
        protected Response m_response;        

        public Rule()
        {
            baseType = BaseType.RULE;
        }

        public override JObject ToJson()
        {
            var jObj = new JObject();

            jObj.Add(new JProperty("TYPE", "MATCHER"));

            var jArrMatch = new JArray();
            foreach(var m in m_matchers)
            {
                jArrMatch.Add(m.ToJson());
            }

            jObj.Add(new JProperty("MATCHERS", jArrMatch));

            var jObjCalled = new JObject();
            jObjCalled.Add(new JProperty("AT_LEAST", m_calledAtLeast));
            jObjCalled.Add(new JProperty("AT_MOST", m_calledAtMost));
            jObj.Add(new JProperty("CALLED_TIMES", jObjCalled));

            jObj.Add(new JProperty("RESPONSE", m_response.ToJson()));

            return jObj;        
        }


        public Rule MatchTimes(int times)
        {
            m_calledAtLeast = times;
            m_calledAtMost = times;
            return this;
        }


        public Rule MatchAtLeast(int times)
        {
            m_calledAtLeast = times;
            return this;
        }

        public Rule MatchAtMost(int times)
        {
            m_calledAtMost = times;
            return this;
        }

        public Rule MatchTimesRange(int t1, int t2)
        {
            m_calledAtLeast = t1;
            m_calledAtMost = t2;
            return this;
        }

        public Rule Method(string method)
        {
            var m = new Matcher(Matcher.MatchType.METHOD, method);
            m_matchers.Add(m);
            return this;
        }

        public Rule Url(string url)
        {
            var m = new Matcher(Matcher.MatchType.URL, url);
            m_matchers.Add(m);
            return this;
        }


        public Rule Header(string headerName, string headerValue)
        {
            var m = new Matcher(Matcher.MatchType.HEADER, headerName, headerValue);
            m_matchers.Add(m);
            return this;
        }

        public Rule Date(string data)
        {
            var m = new Matcher(Matcher.MatchType.DATA, data);
            m_matchers.Add(m);
            return this;
        }

        public Rule RespondWith(Response response)
        {
            m_response = response;
            return this;
        }

    }

    public class Collection : ExpectBase
    {
        protected enum CollectionType { ALL_IN_ORDER, ALL_IN_ANY_ORDER, ANY_NUMBER };
        protected CollectionType m_type = CollectionType.ALL_IN_ORDER;
        protected int m_times = 1;
        protected int m_maxNum = 1;
        protected List<Rule> m_rules = new List<Rule>();

        public Collection()
        {
            baseType = BaseType.COLLECTION;
        }

        public override JObject ToJson()
        {
            var jObj = new JObject();
            jObj.Add(new JProperty("TYPE", "COLLECTION"));
            jObj.Add(new JProperty("COLLECTION_TYPE", m_type.ToString()));
            jObj.Add(new JProperty("CALLED_TIMES", m_times));
            jObj.Add(new JProperty("MAX_NUMBER", m_times));

            var jArrRules = new JArray();
            foreach(var r in m_rules)
            {
                jArrRules.Add(r.ToJson());
            }
            jObj.Add(new JProperty("RULES", jArrRules));

            return jObj;        
        }

        public Collection ExpectAllInOrder()
        {
            m_type = CollectionType.ALL_IN_ORDER;
            return this;
        }

        public Collection ExpectAllInAnyOrder()
        {
            m_type = CollectionType.ALL_IN_ANY_ORDER;
            return this;
        }

        public Collection ExpectAnyNumber(int maxNum)
        {
            m_type = CollectionType.ANY_NUMBER;
            m_maxNum = maxNum;
            return this;
        }

        public Collection AddRule(Rule r)
        {
            m_rules.Add(r);
            return this;
        }
    }
}