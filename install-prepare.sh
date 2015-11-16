#!/bin/bash

chmod +x *.sh *.py
sudo apt-get install -y python3-pip libudev-dev
sudo pip-3.2 install python-uinput pyudev

#if pip-3.2 can't be found, please use pip3
#sudo pip3 install python-uinput pyudev