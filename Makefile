OWNER=nielsbohr
IMAGE=mcweb
TAG=edge

.PHONY: build

all: clean build test

build:
	docker build -t $(OWNER)/$(IMAGE):$(TAG) hub/

clean:
	docker rmi -f $(OWNER)/$(IMAGE):$(TAG)

push:
	docker push ${OWNER}/${IMAGE}:${TAG}