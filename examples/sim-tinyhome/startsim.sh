#!/bin/sh

cd $1 && ln -s ../genEPJ . &&  cp -rL ../makefile ../*genEPJ.py ../*.idf . && exec make
