#!/bin/bash

npm install
npm rebuild node-sass
exec "$@"
