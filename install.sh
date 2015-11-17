#!/bin/bash

echo "Set execution bit..."
chmod +x *.sh *.py

echo "Copy user-space driver and start as service script..."
sudo cp touch.py /usr/bin/
sudo cp touch.sh /etc/init.d/

echo "Apply execution bit to driver file and service script..."
sudo chmod +x /usr/bin/touch.py
sudo chmod +x /etc/init.d/touch.sh

echo "Set service to start driver at boot time...."
sudo update-rc.d touch.sh defaults

echo "Done."