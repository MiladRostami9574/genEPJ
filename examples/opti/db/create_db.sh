#!/usr/bin/env sh

DBNAME=data.db3
CONFIG=config.sql

rm -f $DBNAME

sqlite3 $DBNAME < $CONFIG
