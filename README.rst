poradnia
==============================

.. image:: https://codeclimate.com/github/watchdogpolska/poradnia/badges/gpa.svg
   :target: https://codeclimate.com/github/watchdogpolska/poradnia
   :alt: Code Climate

.. image:: https://requires.io/github/watchdogpolska/poradnia/requirements.svg?branch=master
     :target: https://requires.io/github/watchdogpolska/poradnia/requirements/?branch=master
     :alt: Requirements Status

.. image:: https://img.shields.io/badge/translations-pl%20|%20en-brightgreen.svg
     :target: https://crowdin.com/project/poradnia
     :alt: Translations

.. image:: https://img.shields.io/github/issues/watchdogpolska/poradnia.svg
     :target: https://github.com/watchdogpolska/poradnia/issues
     :alt: GitHub issues counter
     
.. image:: https://img.shields.io/github/license/watchdogpolska/poradnia.svg
     :alt: License

.. image:: https://badge.waffle.io/watchdogpolska/poradnia.svg?label=high&title=High 
     :target: https://waffle.io/watchdogpolska/poradnia 
     :alt: 'Stories in High'

.. image:: https://www.quantifiedcode.com/api/v1/project/0b4753d4b3bd41f797b40458c3cea67a/badge.svg
  :target: https://www.quantifiedcode.com/app/project/0b4753d4b3bd41f797b40458c3cea67a
  :alt: Code issues

.. image:: https://coveralls.io/repos/watchdogpolska/poradnia/badge.svg?branch=master&service=github
  :target: https://coveralls.io/github/watchdogpolska/poradnia?branch=master 

Settings
------------

poradnia relies extensively on environment settings which **will not work with Apache/mod_wsgi setups**. It has been deployed successfully with both Gunicorn/Nginx and even uWSGI/Nginx.

Getting up and running
----------------------

The steps below will get you up and running with a local development environment. We assume you have the following installed:

* pip
* virtualenv
* MySQL

First make sure to create and activate a virtualenv_, then open a terminal at the project root and install the requirements for local development::

    $ pip install -r requirements/local.txt

.. _virtualenv: http://docs.python-guide.org/en/latest/dev/virtualenvs/

Nex to set up enviroment variables
    $ export DJANGO_SETTINGS_MODULE="config.local"
    $ export DATABASE_URL="mysql://user:pass@localhost/poradnia"

You can now run the usual Django ``runserver`` command (replace ``yourapp`` with the name of the directory containing the Django project)::

    $ python poradnia/manage.py runserver

To run tests use: 
    $ function run_test(){ DATABASE_URL="sqlite://" DJANGO_SETTINGS_MODULE='config.tests' python manage.py test $@ -v2}
    $ run_test poradnia

**Live reloading and Sass CSS compilation**

If you'd like to take advantage of live reloading and Sass / Compass CSS compilation you can do so with the included Gulpfile task.

Make sure that nodejs_ is installed. Then in the project root run::

.. note::
    TODO

It's time to write the code!!!


Deployment
------------

It is possible to deploy to Heroku or to your own server by using Dokku, an open source Heroku clone. The recomend way is using Virtual Private Server with Ubuntu Server and Nginx.
