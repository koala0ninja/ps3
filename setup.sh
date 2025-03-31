#!/bin/bash

echo ">>> Updating package lists..."
apt update

echo ">>> Installing required packages (Python, PIP, Git, Bluetooth, Pygame dependencies, Minimal X)..."
apt install -y python3 python3-pip git bluez joystick \
               libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
               libportmidi-dev libfreetype6-dev libmtdev-dev \
               xserver-xorg-core xserver-xorg-input-all xserver-xorg-video-fbdev \
               xinit x11-xserver-utils --no-install-recommends

echo ">>> Installing Pygame..."
pip3 install pygame

# Optional: Install sixpair if modern BlueZ pairing is problematic (uncomment if needed)
# echo ">>> Attempting to install sixpair (may require manual steps if fails)..."
# apt install -y libusb-dev libbluetooth-dev # Dependencies
# TEMP_DIR=$(mktemp -d)
# cd $TEMP_DIR
# wget http://sourceforge.net/projects/qtsixa/files/plugins/sixpair.c # Find a reliable source for sixpair.c if needed
# gcc -o sixpair sixpair.c -lusb
# cp sixpair /usr/local/bin/
# cd /
# rm -rf $TEMP_DIR
# echo ">>> sixpair potentially installed to /usr/local/bin/"

echo ">>> Setup Complete! System will reboot into the tester after 'sudo reboot'."
echo ">>> Remember to add the auto-start lines to /home/pi/.bashrc if you haven't."
exit 0
