#!/bin/bash

chmod +x *.sh *.py

sudo cp touch.py /usr/bin/
sudo cp touch.sh /etc/init.d/

sudo chmod +x /usr/bin/touch.py
sudo chmod +x /etc/init.d/touch.sh

sudo update-rc.d touch.sh defaults
