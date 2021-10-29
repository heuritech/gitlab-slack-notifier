BASE_IMAGE := gitlabnotifier
REGISTRY := heuritech/
ifeq ($(origin CI_COMMIT_SHORT_SHA), undefined)
BUILDTAG := ${USER}
REGISTRY_PREFIX :=
else
BUILDTAG := $(shell echo ${CI_COMMIT_TIMESTAMP} | cut -d'+' -f 1 | tr T . | tr -d :)-$(CI_COMMIT_SHORT_SHA)
REGISTRY_PREFIX := heuritech-dev/
endif

help: ## Display all options of the Makefile
	@grep -E '^[a-zA-Z_-]+%?:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

build-docker: ## Build the docker used for deployment
	docker build  -t ${BASE_IMAGE}:${BUILDTAG} .

build-docker-test: build-docker ## Build the docker used for unit tests
	docker build -f test/Dockerfile --build-arg BASE_IMAGE="${BASE_IMAGE}:${BUILDTAG}" -t ${REGISTRY_PREFIX}${BASE_IMAGE}-test:${BUILDTAG} .

push-docker: ## Push the docker image to the prod registry
	$(eval FULL_IMAGE=${REGISTRY}/${BASE_IMAGE}:$(shell date +%Y-%m-%d.%H%M%S))
	docker tag ${BASE_IMAGE}:${BUILDTAG} ${FULL_IMAGE}
	docker push ${FULL_IMAGE}

push-docker-test: ## Push the docker used for test. Useful in the CI
	docker push ${REGISTRY_PREFIX}${BASE_IMAGE}-test:${BUILDTAG}

run-docker: build-docker ## Build and run the deployment docker
	docker run -p ${HOST}:${PORT}:5000 -e GITLAB_TOKEN -e SLACK_API_TOKEN ${BASE_IMAGE}:${BUILDTAG}

run-docker-test: ## Run test docker
	docker run ${REGISTRY_PREFIX}${BASE_IMAGE}-test:${BUILDTAG}

.DEFAULT_GOAL := help # This line ensures that if you do `make`, the documentation for all operations will be displayed
