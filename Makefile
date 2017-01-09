install:
	pip install -r requirements/production.txt

install_os:
	apt-get install python2.7 mariadb-server git libmariadbclient-dev virtualenv python-dev libffi-dev libssl-dev libjpeg-dev libpng12-dev libxml2-dev libxslt1-dev build-essential libjpeg62

install_devs:
	pip install -r requirements/local.txt
	pip install -r requirements/test.txt

test:
	time python poradnia/manage.py test --keepdb

makemigrations:
	python poradnia/manage.py makemigrations

migrate:
	python poradnia/manage.py migrate

test_parallel:
	time python poradnia/manage.py test --keepdb --parallel $(grep -c ^processor /proc/cpuinfo)

coverage:
	coverage run --branch --omit=*/site-packages/* poradnia/manage.py test --verbosity=2 --keepdb

coverage_html: coverage
	coverage html
	x-www-browser htmlcov/index.html

server:
	python poradnia/manage.py runserver

drop_test_databases:
	echo "drop database test_poradnia; drop database test_poradnia_1; drop database test_poradnia_2; drop database test_poradnia_3; drop database test_poradnia_4;" | python poradnia/manage.py dbshell
