@echo off
rem Helper script for running editfile.py on Windows
pushd %~dp0
python editfile.py "%1"
popd
rem pause
