using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
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

        public void Disconnect()
        {
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
            int intValue;
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
        protected int m_uid;

        public HttpServer(CommandClient owner, int uid)
        {
            m_owner = owner;
            m_uid = uid;
        }

    }



    public class BaseCommand
    {
        public uint UID { get; set; }
        public string COMMAND { get; set; }
        public string COMMAND_DATA { get; set; }        

    }
}