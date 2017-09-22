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

Został opracowany playbook Ansible, który zapewnia wdrożenie aplikacji. Przedstawia on także podstawowe kroki, które są konieczne do uruchomienia aplikacji. Dostępny jest on w pliku ``vagrant_provision_ansible.yaml``. Zalecane jest wykorzystanie przedstawionego playbooka wraz z środowiskiem wirtualizacyjnym Vagrant. Wówczas konfiguracja całego środowiska to::

    $ vagrant up --provision
    $ vagrant ssh
    vagrant@vagrant:/vagrant$ python manage.py runserver 0.0.0.0:8000

Następnie można przejśc w przeglądarce pod adres ``http://localhost:8000``.

Po zakończeniu pracy można wykonać w celu skasowania wirtualnej maszyny::

    $ vagrant destroy

Alternatywnie w celu zaoszczędzenia pamięci RAM można ją wyłącznie uśpić::

    $ vagrant suspend

Warto także zwrócić uwagę na polecenie zapewniające utworzenie użytkownika administracyjnego::

    vagrant@vagrant:/vagrant$ python manage.py createsuperuser

Jeżeli zepsujesz sobie bazę danych wykonaj::

    vagrant@vagrant:/vagrant$ sudo -H mysql 'drop database poradnia';
    $ vagrant provision

Jeżeli chcesz skonfigurować maszynę od nowa wykonaj::

    $ vagrant destroy -f && vagrant up --provision

Jeżeli chcesz upewnić się co do aktualności konfiguracji możesz wykonać::

    $ vagrant provision

Deployment
------------

It is possible to deploy to Heroku or to your own server by using Dokku, an open source Heroku clone. The recomend way is using Virtual Private Server with Ubuntu Server and Nginx.
