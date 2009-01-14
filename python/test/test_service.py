# Copyright (c) 2008 Eric Evans <eevans@racklabs.com>
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

from protobufrpc import tx
from twisted.trial import unittest
from twisted.internet import reactor
from twisted.internet.protocol import ClientCreator
from test_suite_pb2 import Test, Test_Stub, EchoRequest, EchoResponse

class TestService( Test ):
	def Echo( self, rpc_controller, request, done ):
		response = EchoResponse()
		response.text = request.text
		done( response )

class ServiceTestCase( unittest.TestCase ):
	def setUp( self ):
		self.service = TestService()
		self.udp_proto = tx.UdpChannel()
		self.udp_proto.add_service( self.service )
		self.factory = tx.Factory( self.service )
		self.tcp_listener = reactor.listenTCP( 0, self.factory )
		self.udp_listener = reactor.listenUDP( 0, self.udp_proto )
		self.udp_proxy_port = None
		self.tcp_proxy_proto = None

	def tearDown( self ):
		if self.udp_proxy_port:
			self.udp_proxy_port.stopListening()
		if self.tcp_proxy_proto:
			self.tcp_proxy_proto.transport.loseConnection()
		self.tcp_listener.stopListening()
		self.udp_listener.stopListening()

	def testTcpRpc( self ):
		def connected( protocol ):
			self.tcp_proxy_proto = protocol
			text = "TCP Test"
			request = EchoRequest()
			request.text = text
			proxy = tx.Proxy( Test_Stub( protocol ) )
			echoed = proxy.Test.Echo( request )
			echoed.addCallback( lambda r: self.assertEquals( r.text, text ) )
			return echoed

		client = ClientCreator( reactor, tx.TcpChannel )
		d = client.connectTCP( self.tcp_listener.getHost().host,
			self.tcp_listener.getHost().port )
		d.addCallback( connected )
		return d

	def testUdpRpc( self ):
		protocol = tx.UdpChannel( self.udp_listener.getHost().host, 
			self.udp_listener.getHost().port )
		proxy = tx.Proxy( Test_Stub( protocol ) )
		self.udp_proxy_port = reactor.listenUDP( 0, protocol )
		text = "UDP Test"
		request = EchoRequest()
		request.text = text
		echoed = proxy.Test.Echo( request )
		echoed.addCallback( lambda r: self.assertEquals( r.text, text ) )
		return echoed

