STACK_NAME:= ticket-grooming-automation
REGION:= us-east-1
TEMPLATE_FILE:= ./infrastructure/template.yaml
BUILD_DIR:= .aws-sam/build
PARAMETERS_FILE:= parameters.json
S3_BUCKET:= ticket-grooming-automation-artifacts
LAYERS_DIR:= layers
REQUIREMENTS_FILE:= src/layers/requirements.txt

.PHONY: all
all: build package deploy

.PHONY: create-layer
create-layer:
	mkdir -p $(LAYERS_DIR)/python
	pip install --platform manylinux2014_x86_64 --target=$(LAYERS_DIR)/python --implementation cp --python-version 3.9 --only-binary=:all: --upgrade -r $(REQUIREMENTS_FILE)
	cd $(LAYERS_DIR) && zip -r ../jira-layer.zip .
	aws lambda publish-layer-version \
		--layer-name jira-layer \
		--description "Jira Python SDK and dependencies" \
		--zip-file fileb://jira-layer.zip \
		--compatible-runtimes python3.9 \
		--region $(REGION)

.PHONY: build
build:
	sam build --template $(TEMPLATE_FILE) --build-dir $(BUILD_DIR) --base-dir .

.PHONY: create-bucket
create-bucket:
	aws s3api head-bucket --bucket $(S3_BUCKET) --region $(REGION) 2>/dev/null || aws s3 mb s3://$(S3_BUCKET) --region $(REGION)

.PHONY: package
package: create-bucket
	sam package --template-file $(BUILD_DIR)/template.yaml \
	--output-template-file $(BUILD_DIR)/packaged.yaml \
	--s3-bucket $(S3_BUCKET) \

.PHONY: deploy
deploy:
	@echo "Deploying AWS SAM application..."
	@JQL_QUERY=$$(jq -r '.JqlQuery' $(PARAMETERS_FILE) | sed 's/"/\\"/g') && \
	sam deploy --template-file $(BUILD_DIR)/packaged.yaml \
	--stack-name $(STACK_NAME) \
	--region $(REGION) \
	--capabilities CAPABILITY_IAM \
	--parameter-overrides \
	JiraApiUser="$$(jq -r '.JiraApiUser' $(PARAMETERS_FILE))" \
	JiraApiToken="$$(jq -r '.JiraApiToken' $(PARAMETERS_FILE))" \
	JiraBaseUrl="$$(jq -r '.JiraBaseUrl' $(PARAMETERS_FILE))" \
	BedrockEndpoint="$$(jq -r '.BedrockEndpoint' $(PARAMETERS_FILE))" \
	JqlQuery="$$JQL_QUERY"

.PHONY: destroy
destroy:
	aws cloudformation delete-stack --stack-name $(STACK_NAME) --region $(REGION)

.PHONY: clean
clean:
	rm -rf $(BUILD_DIR) $(LAYERS_DIR) *.zip
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

.PHONY: validate
validate:
	sam validate --template $(TEMPLATE_FILE)
