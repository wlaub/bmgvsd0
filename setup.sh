#!/bin/bash -e

venv=venv

if [ -e $venv ]; then
    echo "already set up"
else
    mkdir $venv
    mkdir stats
    virtualenv $venv --python=3
    source $venv/bin/activate
    pip install pygame pymunk pyyaml
fi
