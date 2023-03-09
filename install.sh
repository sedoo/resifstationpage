#!/bin/sh

if [ -z "$PYENV" ]
then
      echo "\$PYENV is not present"
      exit 1
fi

python3 -m venv $PYENV
. $PYENV/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install matplotlib