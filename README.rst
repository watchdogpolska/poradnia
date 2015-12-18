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

Settings
------------

poradnia relies extensively on environment settings which **will not work with Apache/mod_wsgi setups**. It has been deployed successfully with both Gunicorn/Nginx and even uWSGI/Nginx.

For configuration purposes, the following table maps the 'poradnia' environment variables to their Django setting:

======================================= =========================== ============================================== ===========================================
Environment Variable                    Django Setting              Development Default                            Production Default
======================================= =========================== ============================================== ===========================================
DJANGO_AWS_ACCESS_KEY_ID                AWS_ACCESS_KEY_ID           n/a                                            raises error
DJANGO_AWS_SECRET_ACCESS_KEY            AWS_SECRET_ACCESS_KEY       n/a                                            raises error
DJANGO_AWS_STORAGE_BUCKET_NAME          AWS_STORAGE_BUCKET_NAME     n/a                                            raises error
DJANGO_CACHES                           CACHES                      locmem                                         memcached
DJANGO_DATABASES                        DATABASES                   See code                                       See code
DJANGO_DEBUG                            DEBUG                       True                                           False
DJANGO_EMAIL_BACKEND                    EMAIL_BACKEND               django.core.mail.backends.console.EmailBackend django.core.mail.backends.smtp.EmailBackend
DJANGO_SECRET_KEY                       SECRET_KEY                  CHANGEME!!!                                    raises error
DJANGO_SECURE_BROWSER_XSS_FILTER        SECURE_BROWSER_XSS_FILTER   n/a                                            True
DJANGO_SECURE_SSL_REDIRECT              SECURE_SSL_REDIRECT         n/a                                            True
DJANGO_SECURE_CONTENT_TYPE_NOSNIFF      SECURE_CONTENT_TYPE_NOSNIFF n/a                                            True
DJANGO_SECURE_FRAME_DENY                SECURE_FRAME_DENY           n/a                                            True
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS   HSTS_INCLUDE_SUBDOMAINS     n/a                                            True
DJANGO_SESSION_COOKIE_HTTPONLY          SESSION_COOKIE_HTTPONLY     n/a                                            True
DJANGO_SESSION_COOKIE_SECURE            SESSION_COOKIE_SECURE       n/a                                            False
======================================= =========================== ============================================== ===========================================

* TODO: Add vendor-added settings in another table

Getting up and running
----------------------

The steps below will get you up and running with a local development environment. We assume you have the following installed:

* pip
* virtualenv
* PostgreSQL

First make sure to create and activate a virtualenv_, then open a terminal at the project root and install the requirements for local development::

    $ pip install -r requirements/local.txt

.. _virtualenv: http://docs.python-guide.org/en/latest/dev/virtualenvs/

You can now run the usual Django ``runserver`` command (replace ``yourapp`` with the name of the directory containing the Django project)::

    $ python yourapp/manage.py runserver

The base app will run but you'll need to carry out a few steps to make the sign-up and login forms work. These are currently detailed in `issue #39`_.

.. _issue #39: https://github.com/pydanny/cookiecutter-django/issues/39

**Live reloading and Sass CSS compilation**

If you'd like to take advantage of live reloading and Sass / Compass CSS compilation you can do so with the included Grunt task.

Make sure that nodejs_ is installed. Then in the project root run::

    $ npm install grunt

.. _nodejs: http://nodejs.org/download/

Now you just need::

    $ grunt serve

The base app will now run as it would with the usual ``manage.py runserver`` but with live reloading and Sass compilation enabled.

To get live reloading to work you'll probably need to install an `appropriate browser extension`_

.. _appropriate browser extension: http://feedback.livereload.com/knowledgebase/articles/86242-how-do-i-install-and-use-the-browser-extensions-

It's time to write the code!!!


Deployment
------------

It is possible to deploy to Heroku or to your own server by using Dokku, an open source Heroku clone. 

Heroku
^^^^^^

Run these commands to deploy the project to Heroku:

.. code-block:: bash

    heroku create --buildpack https://github.com/heroku/heroku-buildpack-python
    heroku addons:create cleardb
    heroku addons:create sendgrid:starter
    heroku addons:create memcachier:dev
    heroku config:set DATABASE_URL=$(heroku config | grep CLEARDB_DATABASE_URL | cut -d ' ' -f2)
    heroku config:set DJANGO_CONFIGURATION=Production
    heroku config:set DJANGO_SETTINGS_MODULE="config"
    heroku config:set DJANGO_SECRET_KEY=RANDOM_SECRET_KEY_HERE
    heroku config:set DJANGO_EMAIL_HOST_USER=$(heroku config | grep SENDGRID_USERNAME | cut -d ' ' -f2)
    heroku config:set DJANGO_EMAIL_HOST_PASSWORD=$(heroku config | grep SENDGRID_PASSWORD | cut -d ' ' -f2)
    heroku config:set DJANGO_SERVER_EMAIL="smtp.sendgrid.com"
    heroku config:set WHITENOISE_USE="True"
    git push heroku master
    heroku run python poradnia/manage.py migrate
    heroku run python poradnia/manage.py createsuperuser
    heroku open

Dokku
^^^^^

You need to make sure you have a server running Dokku with at least 1GB of RAM. Backing services are
added just like in Heroku however you must ensure you have the relevant Dokku plugins installed. 

.. code-block:: bash

    cd /var/lib/dokku/plugins
    git clone https://github.com/rlaneve/dokku-link.git link
    git clone https://github.com/jezdez/dokku-memcached-plugin memcached
    git clone https://github.com/jezdez/dokku-postgres-plugin postgres
    dokku plugins-install

You can specify the buildpack you wish to use by creating a file name .env containing the following.

.. code-block:: bash

    export BUILDPACK_URL=<repository>

You can then deploy by running the following commands.

..  code-block:: bash

    git remote add dokku dokku@yourservername.com:poradnia
    git push dokku master
    ssh -t dokku@yourservername.com dokku memcached:create poradnia-memcached
    ssh -t dokku@yourservername.com dokku memcached:link poradnia-memcached poradnia
    ssh -t dokku@yourservername.com dokku mysql:create poradnia-mysql
    ssh -t dokku@yourservername.com dokku mysql:link poradnia-mysq ploradnia
    ssh -t dokku@yourservername.com dokku config:set .... # See heroku installation
    ssh -t dokku@yourservername.com dokku run poradnia python poradnia/manage.py migrate
    ssh -t dokku@yourservername.com dokku run poradnia python poradnia/manage.py createsuperuser

When deploying via Dokku make sure you backup your database in some fashion as it is NOT done automatically.
