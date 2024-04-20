#!/bin/bash

if [ -z "$2" ]; then
  echo Usage: $0 lock_name [max_ok_delay] command...
  exit 1
fi

LOCKDIR=/var/lock
LOCKNAME=$1
LOCKFILE=${LOCKDIR}/$1.lock
TIMEFILE=${LOCKDIR}/$1.time
shift

exec 99>$LOCKFILE
flock -xn 99 || { \
    echo Lock acquired by other process \
    $(( $(date +%s)-$(cat $TIMEFILE) )) seconds ago, exiting \
    && exit 1; \
}
date +%s > $TIMEFILE
[[ $1 =~ ^[0-9]*[mhd]?$ ]] && { echo $1 > $TIMEFILE.maxokdelay; shift; }
trap "flock -u 99" EXIT

output=$(eval $@)
exitcode=$?

exit $exitcode
