#!/bin/bash

# This script sets up the crontab for the application. To be run when starting app cron container.
APP_ROOT_DIR="${APP_ROOT_DIR:-/code}"
APP_NAME="${APP_NAME:-porady}"
CRON_DIR="${SCRIPT_DIR:-/code/.contrib/docker/cron}"
PTYHON=$(which python3)
SHELL="/bin/bash"

# Set default schedules for the application cron jobs
# The schedules can be overridden by setting the corresponding environment variables
# in app cron container.
# Schedule format: minute hour day month weekday
# or @reboot, @yearly, @annually, @monthly, @weekly, @daily, @midnight, @hourly
EVENT_REMINDERS_SCHEDULE="${EVENT_REMINDERS_SCHEDULE:-0 12 * * *}"
OLD_CASES_REMINDER_SCHEDULE="${OLD_CASES_REMINDER_SCHEDULE:-0 6 2 * *}"
COURT_SESSION_PARSER_SCHEDULE="${COURT_SESSION_PARSER_SCHEDULE:-10 23 * * *}"
CLEARSESSIONS_SCHEDULE="${CLEARSESSIONS_SCHEDULE:-@daily}"

# Set the crontab for the application
echo "
# $APP_NAME-send_event_reminders
$EVENT_REMINDERS_SCHEDULE cd $APP_ROOT_DIR && $CRON_DIR/run_locked.sh $APP_NAME-send_event_reminders 25h \
    \"$PTYHON $APP_ROOT_DIR/manage.py send_event_reminders\" >> /var/log/cron.log 2>&1
# $APP_NAME-send_old_cases_reminder
$OLD_CASES_REMINDER_SCHEDULE cd $APP_ROOT_DIR && $CRON_DIR/run_locked.sh $APP_NAME-send_send_old_cases_reminder 25h \
    \"$PTYHON $APP_ROOT_DIR/manage.py send_old_cases_reminder\" >> /var/log/cron.log 2>&1
# $APP_NAME-run_court_session_parser
$COURT_SESSION_PARSER_SCHEDULE cd $APP_ROOT_DIR && $CRON_DIR/run_locked.sh $APP_NAME-run_court_session_parser 34h \
    \"$PTYHON $APP_ROOT_DIR/manage.py run_court_session_parser\" >> /var/log/cron.log 2>&1
# $APP_NAME-clearsessions
$CLEARSESSIONS_SCHEDULE cd $APP_ROOT_DIR && $CRON_DIR/run_locked.sh $APP_NAME-clearsessions 34h \
    \"$PTYHON $APP_ROOT_DIR/manage.py clearsessions\" >> /var/log/cron.log 2>&1
" | crontab -
 
# The  run_locked.sh  script is a simple wrapper around  flock  that ensures that only one 
# instance of a given command is running at a time. 
# Path: .contrib/docker/cron/run_locked.sh
