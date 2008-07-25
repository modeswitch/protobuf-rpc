#!/bin/sh

protoc -I=./protocol --python_out=./pbrpc ./protocol/pbrpc.proto
