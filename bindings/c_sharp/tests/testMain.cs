using testapi;
using System;
using System.IO;


using Xunit;
using Xunit.Abstractions;

namespace tests
{
    public class UnitTest1
    {

        [Fact]
        public void Test1()
        {
          var cmd = new testapi.CommandClient();
          Assert.True(cmd.connect());
        }
    }
}
/*
namespace tests
{
    public class Tests
    {
        [SetUp]
        public void Setup()
        {
          Console.WriteLine("Setup");

          var cmd = new testapi.CommandClient();
          cmd.connect();
        }

        [Test]
        public void Test1()
        {
            Assert.Pass();
        }
    }
}
*/
