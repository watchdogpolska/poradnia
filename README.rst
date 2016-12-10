poradnia
==============================

.. image:: https://codeclimate.com/github/watchdogpolska/poradnia/badges/gpa.svg
   :target: https://codeclimate.com/github/watchdogpolska/poradnia
   :alt: Code Climate

.. image:: https://pyup.io/repos/github/watchdogpolska/poradnia/shield.svg
     :target: https://pyup.io/repos/github/watchdogpolska/poradnia/
     :alt: Updates

.. image:: https://img.shields.io/github/issues/watchdogpolska/poradnia.svg
     :target: https://github.com/watchdogpolska/poradnia/issues
     :alt: GitHub issues counter
     
.. image:: https://img.shields.io/github/license/watchdogpolska/poradnia.svg
     :alt: License

.. image:: https://coveralls.io/repos/watchdogpolska/poradnia/badge.svg?branch=master&service=github
  :target: https://coveralls.io/github/watchdogpolska/poradnia?branch=master 

.. image:: https://badges.gitter.im/watchdogpolska/poradnia.svg
  :target: https://gitter.im/watchdogpolska/poradnia?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge 
  :alt: Gitter

Settings
------------

poradnia relies extensively on environment settings which **will not work with Apache/mod_wsgi setups**. It has been deployed successfully with both Gunicorn/Nginx and even uWSGI/Nginx.

Getting up and running
----------------------

The steps below will get you up and running with a local development environment. We assume you have the following installed
First make sure to install all requires OS-level libraries and application (dependencies)::

    $ make install_os

Next to create and activate a virtualenv_::

    $ virtualenv env
    $ source env/bin/activate

    .. _virtualenv: http://docs.python-guide.org/en/latest/dev/virtualenvs/

Next to open a terminal at the project root and install the requirements for local development::

    $ make install_devs

Next to create MySQL database::

    # if you are using Ubuntu 14.04, you may need to find a workaround for the following two commands
    $ sudo systemctl start mariadb
    $ sudo systemctl enable mariadb
    
    $ mysql_tzinfo_to_sql /usr/share/zoneinfo | mysql -u root mysql
    
    $ echo "CREATE DATABASE poradnia CHARACTER SET utf8 COLLATE utf8_polish_ci;" | mysql -u root
    $ echo "CREATE USER 'user'@'localhost' IDENTIFIED BY 'pass';" | mysql -u root
    $ echo "GRANT ALL PRIVILEGES ON poradnia . * TO 'user'@'localhost'; FLUSH PRIVILEGES;" | mysql -u root

Next to set up enviroment variables::

    $ export DATABASE_URL="mysql://user:pass@localhost/poradnia"

Next to push migrations into database::

    $ make migrate

You can now run the usual Django ``runserver`` command::

    $ make server

To run tests use::

    $ make test

If you like you can use run tests in parallel by use::

    $ make test_parallel


**Live reloading and Sass CSS compilation**

If you'd like to take advantage of live reloading and Sass / Compass CSS compilation you can do so with the included Gulpfile task.

Make sure that nodejs_ is installed. Then in the project root run::

.. note:: TODO (see issue #207)

It's time to write the code!!!

Deployment
------------

It is possible to deploy to Heroku or to your own server by using Dokku, an open source Heroku clone. The recomend way is using Virtual Private Server with Ubuntu Server and Nginx.
