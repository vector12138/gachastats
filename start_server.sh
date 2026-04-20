#!/bin/bash
export DISPLAY=:10
cd /home/void/prj/gachastats
source ~/.venvs/gachastats/bin/activate
exec python run.py
