.PHONY: list test run stop

DOCKER_FILE = Dockerfile
DOCKER_IMAGE = keykeeper_image
DOCKER_CONTAINER = keykeeper_container

list:
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$'


run:
	yes|docker image prune
	yes|docker container prune
	docker buildx build -f $(DOCKER_FILE) -t $(DOCKER_IMAGE) --load .
	clear
	mkdir -p tmp
	docker run --rm -d \
	-p 8080:7012 \
	--volume $(shell pwd)/tmp:/data \
	--name $(DOCKER_CONTAINER) \
	--env LOGLEVEL=INFO \
	--env TZ=Europe/Berlin \
	$(DOCKER_IMAGE) --host=0.0.0.0 --port=7012 --db_file=/data/sqlite.bin --db_key="4NHH7D3+0AoSPXb2I6byPg=="


stop:
	docker container stop $(DOCKER_CONTAINER)


terminal:
	make run
	- docker exec -it $(DOCKER_CONTAINER) /bin/bash
	docker container stop $(DOCKER_CONTAINER)


test:
	pytest -s
	echo -e "\a"
