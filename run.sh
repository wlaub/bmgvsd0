#!/bin/bash 

source venv/bin/activate

checksum=`git rev-parse --short HEAD`
status=`git status --porcelain --untracked-files=no | wc -l`
if [ -z $status ]; then
    title=$checksum
else
    title=$checksum"+"
fi


python main.py $title
