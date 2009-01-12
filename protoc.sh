#!/bin/sh

protoc -I=./protocol --python_out=./python/protobufrpc ./protocol/protobufrpc.proto
