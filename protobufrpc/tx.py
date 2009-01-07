# Copyright (c) 2008 Alan Kligman
# Copyright (c) 2008 Johan Euphrosine
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

import twisted.internet.protocol
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.protocols.basic import Int32StringReceiver
import google.protobuf.service
from protobufrpc.protobufrpc_pb2 import Rpc, Request, Response, Error
from protobufrpc.common import Controller

def flatten( l ):
	result = []
	for i in l:
		if hasattr( i, "__iter__" ) and not isinstance( i, basestring ):
			result.extend( flatten( i ) )
		else:
			result.append( i )
	return result

class Protocol( google.protobuf.service.RpcChannel, Int32StringReceiver ):
	id = 0
	def __init__( self ):
		google.protobuf.service.RpcChannel.__init__( self )
		self._pending = {}
	
	def CallMethod( self, methodDescriptor, rpcController, request, responseClass, done ):
		self.id += 1
		d = Deferred()
		d.addCallback( self.unserialize_response, responseClass )
		d.addCallback( done )
		self._pending[ self.id ] = d
		rpc = Rpc()
		rpcRequest = rpc.request.add()
		rpcRequest.method = methodDescriptor.containing_service.name + '.' + methodDescriptor.name
		rpcRequest.serialized_request = request.SerializeToString()
		rpcRequest.id = self.id
		self.sendString( rpc.SerializeToString() )

	def stringReceived( self, data ):
		rpc = Rpc()
		rpc.ParseFromString( data )
		for serializedRequest in rpc.request:
			service = self._services[ serializedRequest.method.split( '.' )[ 0 ] ]
			method = service.GetDescriptor().FindMethodByName( serializedRequest.method.split( '.' )[ 1 ] )
			if method:
				request = service.GetRequestClass( method )()
				request.ParseFromString( serializedRequest.serialized_request )
				controller = Controller()
				d = Deferred()
				d.addCallback( self.serialize_response, serializedRequest )
				d.addCallback( self.serialize_rpc )
				d.addCallback( lambda rpc: self.sendString( rpc.SerializeToString() ) )
				service.CallMethod( method, controller, request, d.callback )
		for serializedResponse in rpc.response:
			id = serializedResponse.id
			if self._pending.has_key( id ):
				self._pending[ id ].callback( serializedResponse )
	
	def unserialize_response( self, serializedResponse, responseClass ):
		response = responseClass()
		response.ParseFromString( serializedResponse.serialized_response )
		return response
	
	def serialize_response( self, response, serializedRequest ):
		serializedResponse = Response()
		serializedResponse.id = serializedRequest.id
		serializedResponse.serialized_response = response.SerializeToString()
		return serializedResponse
	
	def serialize_rpc( self, serializedResponse ):
		rpc = Rpc()
		rpcResponse = rpc.response.add()
		rpcResponse.serialized_response = serializedResponse.serialized_response
		rpcResponse.id = serializedResponse.id
		return rpc
	
class Factory( twisted.internet.protocol.Factory ):
	protocol = Protocol

	def __init__( self, *services ):
		self._protocols = []
		self._services = {}
		for s in services:
			self._services[ s.GetDescriptor().name ] = s
	
	def buildProtocol( self, addr ):
		p = self.protocol()
		p.factory = self
		p._services = self._services
		self._protocols.append( p )
		return p

class Proxy( object ):
	class _Proxy( object ):
		def __init__( self, stub ):
			self._stub = stub

		def __getattr__( self, key ):
			def call( method, request ):
				d = Deferred()
				controller = Controller()
				method( controller, request, d.callback )
				return d
			return lambda request: call( getattr( self._stub, key ), request )

	def __init__( self, *stubs ):
		self._stubs = {}
		for s in stubs:
			self._stubs[ s.GetDescriptor().name ] = self._Proxy( s )
	
	def __getattr__( self, key ):
		return self._stubs[ key ]

class Server( object ):
	def __init__( self, service, port, iface = '' ):
		self._service = service
		self._factory = Factory( self._service )
		self._port = reactor.listenTCP( port, self._factory, 50, iface )
		self._protocols = []
	
	def shutdown( self ):
		for protocol in self._protocols:
			protocol.transport.loseConnection()
		for protocol in self._factory._protocols():
			protocol.transport.loseConnection()
		self._port.stopListening()
