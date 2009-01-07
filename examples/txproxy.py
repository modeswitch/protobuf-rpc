# Copyright (c) 2008 Alan Kligman
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from test_pb2 import *
from twisted.internet import reactor
from twisted.internet.defer import Deferred, DeferredList
from twisted.internet.protocol import ClientCreator
from pbrpc.tx import Protocol, Proxy
from google.protobuf.text_format import *

if __name__ == "__main__":
	c = ClientCreator( reactor, Protocol )
	d = c.connectTCP( "localhost", 8080 )
	def print_response( response ):
		print "response:", MessageToString( response )
	def client_connected( protocol ):
		proxy = Proxy( Test_Stub( protocol ), Math_Stub( protocol ))

		request = EchoRequest()
		request.text = "Hello world!"
		echoed = proxy.Test.Echo( request )
		echoed.addCallback( print_response )

		request = PingRequest()
		pinged = proxy.Test.Ping( request )
		pinged.addCallback( print_response )

		request = MathBinaryOperationRequest()
		request.first = 2;
		request.second = 2;
		mathAddd = proxy.Math.Add( request )
		mathAddd.addCallback( print_response )

		mathMultiplyd = proxy.Math.Multiply( request )
		mathMultiplyd.addCallback( print_response )

		dl = DeferredList( [ echoed, pinged, mathAddd, mathMultiplyd ] )
		dl.addCallback( client_finished )

		return dl
	def client_finished( dl ):
		reactor.stop()
	d.addCallback( client_connected )
	
	reactor.run()
