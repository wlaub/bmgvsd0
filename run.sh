#!/bin/bash

source venv/bin/activate

checksum=`git rev-parse --short HEAD`
if [ -z `git status --porcelain` ]; then
    title=$checksum
else
    title=$checksum"+"
fi

python main.py $title
