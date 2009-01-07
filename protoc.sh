#!/bin/sh

protoc -I=./protocol --python_out=./protobufrpc ./protocol/protobufrpc.proto
