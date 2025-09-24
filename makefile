# Makefile for Django project commands using dev settings

venv-activate:
	@echo "To activate virtualenv, run:"
	@echo "source .venv/bin/activate"

install:
	pip install -r requirements/dev.txt

migrate:
	python manage.py migrate --settings=config.settings.dev

makemigrations:
	python manage.py makemigrations --settings=config.settings.dev

createsuperuser:
	python manage.py createsuperuser --settings=config.settings.dev

runserver:
	python manage.py runserver --settings=config.settings.dev

shell:
	python manage.py shell --settings=config.settings.dev

test:
	python manage.py test --settings=config.settings.dev

# Create Django project (run once, specify PROJECT_NAME)
startproject:
	django-admin startproject $(PROJECT_NAME) .


# Create new app normally (in current directory, specify APP_NAME)
startapp-normal:
	python manage.py startapp $(APP_NAME)	

# Create new app inside apps/ folder (specify app name with lowercase)
dev-startapp:
	cd apps && python3 ../manage.py startapp $(app) --settings=config.settings.dev

# Run tests for a specific test module or file
dev-test-file:
	python3 manage.py test $(test_file) --settings=config.settings.dev

	
