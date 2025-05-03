export PYTHONPATH := .

.PHONY: help
help: ## Show this help
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: venv
venv:				 	## Create virtual environment
						python3 -m venv venv && \
						./venv/bin/pip install --upgrade pip && \
						./venv/bin/pip install -r requirements.txt

.PHONY: clean
clean:					## Removes virtual environment
						test -d venv && rm -rf venv

.PHONY: check_db
check_db: 				## Run pre-start script to check database
	 					python ./main/backend_pre_start.py

.PHONY: runserver
runserver:				## Run FastAPI server with reload option enabled
	 					uvicorn main.app:app --host 0.0.0.0 --port 5000 --reload

.PHONY: runserver_docker
runserver_docker:		## Run FastAPI server with reload option disabled
	 					uvicorn main.app:app --host 0.0.0.0 --port 5000

.PHONY: migration
migration:				## Generates migration commit file in versions folder
						alembic revision --autogenerate -m "$(message)"

.PHONY: migrate
migrate:				## Executes migration commit file to the database
						alembic upgrade head

.PHONY: docker_build
docker_build:			## Builds, (re)creates, and starts the container
						docker compose up -d --force-recreate --build

.PHONY: docker_up
docker_up:				## Builds and starts the container
						docker compose up -d

.PHONY: docker_start
docker_start:			## Starts existing container
						docker compose start

.PHONY: docker_down
docker_down:			## Stop the container
						docker compose down

.PHONY: docker_remove_dangling_images
docker_remove_dangling_images:	## Removes dangling docker images
								docker images --filter "dangling=true" -q --no-trunc | xargs docker rmi
