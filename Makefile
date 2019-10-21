clean:
	docker-compose down

build:
	docker-compose build web

test:
	docker-compose run web python manage.py test --keepdb --verbosity=2

wait_mysql:
	docker-compose run web bash -c 'wait-for-it db:3306'

migrate:
	docker-compose run web python manage.py migrate

lint:
	docker run --rm -v $$(pwd):/data cytopia/black --check /data

fmt:
	docker run --rm -v $$(pwd):/data cytopia/black /data

check: wait_mysql
	docker-compose run web python manage.py makemigrations --check

migrations: wait_mysql
	docker-compose run web python manage.py makemigrations

settings:
	docker-compose run web python manage.py diffsettings

docs:
	docker-compose run web sphinx-build -b html -d docs/_build/doctrees docs docs/_build/html