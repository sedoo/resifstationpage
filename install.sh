#!/bin/sh

if [ -z "$PYENV" ]
then
      echo "\$PYENV is not present"
      exit 1
fi

python3 -m venv $PYENV
. $PYENV/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install matplotlib==3.7.1
python3 -m pip install ObsPy==1.4.0
python3 -m pip install docopt==0.6.2
python3 -m pip install geojson==3.0.1
python3 -m pip install shutils
