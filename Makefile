install:
	pip install -r requirements/production.txt

install_devs:
	pip install -r requirements/local.txt
	pip install -r requirements/test.txt

test:
	time python poradnia/manage.py test --keepdb

test_parallel:
	time python poradnia/manage.py test --keepdb --parallel $(grep -c ^processor /proc/cpuinfo)

coverage:
	time python poradnia/manage.py test --keepdb
	coverage run --branch --omit=*/site-packages/* manage.py test --verbosity=2 --keepdb

coverage_html: coverage
	coverage html
	x-www-browser htmlcov/index.html

server:
	python poradnia/manage.py runserver

drop_test_databases:
	echo "drop database test_poradnia; drop database test_poradnia_1; drop database test_poradnia_2; drop database test_poradnia_3; drop database test_poradnia_4;" | python manage.py dbshell
