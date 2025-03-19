#!/bin/bash

# Set Defaults
BUILD_DIR=./build

# Gather all galaxy.yml files
GALAXY_FILES=`find . -name galaxy.yml`

for file in $GALAXY_FILES; do
    COLL_DIR=`dirname $file`
    COLL_FILE=`basename $file`
    echo "Building $COLL_DIR"

    ansible-galaxy collection build --output-path $BUILD_DIR $COLL_DIR
done
