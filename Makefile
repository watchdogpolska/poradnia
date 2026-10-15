TEST=

db:
	docker compose up -d --remove-orphans db

start: wait_mysql
	docker compose up

runserver: run-background
	docker compose exec web python manage.py runserver 0.0.0.0:8000

run-background: wait_mysql
	docker compose up -d

stop:
	docker compose stop

clean:
	docker compose down

build:
	docker compose build

gulp:
	docker compose run --remove-orphans web python manage.py collectstatic --no-input
	docker compose up --remove-orphans gulp
	docker compose run --remove-orphans web python manage.py collectstatic --no-input

test: wait_mysql
	docker compose exec -t db mysql --user=root --password=password -e "DROP DATABASE IF EXISTS test_poradnia;"
	docker compose run web python manage.py test --keepdb --verbosity=2 --exclude-tag=live ${TEST}

e2e: wait_mysql
	docker compose --file docker-compose.yml --file docker-compose.test.yml up --build --exit-code-from tests db web tests

# Regenerate the committed WCAG normal-mode baseline (tests/wcag/playwright/baseline/)
# before committing a PR that changes normal-mode output - see
# logs/wcag/README.md §4-5 for what gets committed (HTML + assets.sha256) vs
# stays local-only (screenshots). Seeds a throwaway poradnia_a11y database
# (never poradnia/test_poradnia - no real client data), brings the app up
# against it, rebuilds frontend assets, then runs the Playwright capture on
# the host (Playwright needs a real Chromium, not the web container) before
# switching the web container back to its normal (non-a11y) config.
wcag-baseline: A11Y_SEED_PASSWORD := $(shell openssl rand -base64 24)
wcag-baseline: wait_mysql
	docker compose exec -T db mysql -uroot -ppassword -e \
		"CREATE DATABASE IF NOT EXISTS poradnia_a11y CHARACTER SET utf8mb4 COLLATE utf8mb4_polish_ci;"
	docker compose -f docker-compose.yml -f tests/wcag/docker-compose.a11y.yml \
		run --rm web python manage.py migrate
	docker compose up -d --remove-orphans maildump
	docker compose -f docker-compose.yml -f tests/wcag/docker-compose.a11y.yml \
		run --rm -e A11Y_SEED_PASSWORD="$(A11Y_SEED_PASSWORD)" \
		web python tests/wcag/seed_a11y.py --reset
	docker compose -f docker-compose.yml -f tests/wcag/docker-compose.a11y.yml up -d web
	$(MAKE) gulp
	sha256sum poradnia/static/css/style.css poradnia/static/css/style.min.css \
		poradnia/static/js/script.js poradnia/static/js/script.min.js \
		> tests/wcag/playwright/baseline/assets.sha256
	cd tests/wcag/playwright && npm install && npx playwright install chromium && \
		A11Y_SEED_PASSWORD="$(A11Y_SEED_PASSWORD)" node baseline_capture.js
	docker compose up -d web
	@echo ""
	@echo "Baseline regenerated. Review before committing:"
	@echo "  git status tests/wcag/playwright/baseline/"
	@echo "  git diff tests/wcag/playwright/baseline/html/"
	@echo "Commit tests/wcag/playwright/baseline/{html,assets.sha256} if the change is expected."
	@echo "Screenshots (logs/wcag/baseline/screenshots/) are local-only - not committed."

wait_mysql:
	docker compose up -d --remove-orphans db
	docker compose run web bash -c 'wait-for-it db:3306'

migrate:
	docker compose run -e DB_READ_TIMEOUT=300 -e DB_WRITE_TIMEOUT=300 web python manage.py migrate

lint: # lint currently staged files
	docker compose run web pre-commit run

lint-all: # lint all files in repository
	docker compose run web pre-commit run --all-files

check: wait_mysql
	docker compose run web python manage.py makemigrations --check

migrations: wait_mysql
	docker compose run web python manage.py makemigrations

settings:
	docker compose run web python manage.py diffsettings

docs:
	docker compose run web sphinx-build -b html -d docs/_build/doctrees docs docs/_build/html

fulltest: check test e2e

# Celery commands for background task processing
celery-worker: wait_mysql
	docker compose up --remove-orphans rabbitmq celery-worker

celery-beat: wait_mysql
	docker compose up --remove-orphans rabbitmq celery-beat

celery-status:
	docker compose exec celery-worker celery -A config inspect active

celery-purge: # Clear all queues (use with caution)
	docker compose exec celery-worker celery -A config purge

# Start all Celery services together
celery-all: wait_mysql
	docker compose up --remove-orphans rabbitmq celery-worker celery-beat

