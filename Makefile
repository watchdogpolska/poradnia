test:
	docker-compose run web python manage.py test --keepdb
clean:
	rm -r node_modules poradnia/media poradnia/static/js
	mkdir node_modules poradnia/media poradnia/static
