#!/bin/sh
sudo apt update -y
sudo apt upgrade -y
sudo apt install -y python3-dev
sudo apt install -y libssl-dev
wget https://sh.rustup.rs -O /tmp/rust.sh
sh /tmp/rust.sh -y
source "/home/pi/.cargo/env"
wget https://bootstrap.pypa.io/get-pip.py -O /tmp/get-pip.py
python3 /tmp/get-pip.py
python3 -m pip install --user --upgrade pip wheel setuptools
python3 -m pip install --user -r "$md_build/requirements.txt"
