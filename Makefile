TEST=

db:
	docker compose up -d --remove-orphans db

start: wait_mysql
	docker compose up

run-background: wait_mysql
	docker compose up -d

stop:
	docker compose stop

clean:
	docker compose down

build:
	docker compose build web

gulp:
	docker compose run --remove-orphans web python manage.py collectstatic --no-input
	docker compose up --remove-orphans gulp
	docker compose run --remove-orphans web python manage.py collectstatic --no-input

test: wait_mysql
	docker compose exec -t db mysql --user=root --password=password -e "DROP DATABASE IF EXISTS test_poradnia;"
	docker compose run web python manage.py test --keepdb --verbosity=2 ${TEST}

e2e: wait_mysql
	docker compose --file docker-compose.yml --file docker-compose.test.yml up --build --exit-code-from tests db web tests

wait_mysql:
	docker compose up -d --remove-orphans db
	docker compose run web bash -c 'wait-for-it db:3306'

migrate:
	docker compose run web python manage.py migrate

lint: # lint currently staged files
	pre-commit run

lint-all: # lint all files in repository
	pre-commit run --all-files

check: wait_mysql
	docker compose run web python manage.py makemigrations --check

migrations: wait_mysql
	docker compose run web python manage.py makemigrations

settings:
	docker compose run web python manage.py diffsettings

docs:
	docker compose run web sphinx-build -b html -d docs/_build/doctrees docs docs/_build/html

fulltest: check test e2e

