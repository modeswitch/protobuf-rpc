#!/bin/sh

protoc -I=./pbrpc --python_out=./pbrpc ./pbrpc/*.proto
