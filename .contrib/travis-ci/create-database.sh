#!/bin/sh
echo "CREATE DATABASE test_poradnia DEFAULT CHARACTER SET utf8 COLLATE utf8_polish_ci;" | mysql
echo "CREATE DATABASE poradnia DEFAULT CHARACTER SET utf8 COLLATE utf8_polish_ci;" | mysql
