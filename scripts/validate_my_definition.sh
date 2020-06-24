#!/usr/bin/env bash

export TEMP=$(mktemp -d -t alertlogic-sdk-definitions-validation)
python3 -m venv $TEMP
source $TEMP/bin/activate
pip3 install requests jsonschema PyYaml
curl https://raw.githubusercontent.com/anton-b/alertlogic-sdk-definitions/validation-script/scripts/validate_my_definition.py -o $TEMP/validate_my_definition.py
python3 $TEMP/validate_my_definition.py -f $1 && rm -rf $TEMP