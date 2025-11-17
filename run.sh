#!/bin/bash 

source venv/bin/activate

checksum=`git rev-parse --short HEAD`
git status --porcelain > /dev/null
if [ $? ]; then
    title=$checksum"+"
else
    title=$checksum
fi

python main.py $title
