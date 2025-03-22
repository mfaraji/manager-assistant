STACK_NAME:= ticket-grooming-automation
REGION:= us-east-1
TEMPLATE_FILE:= ./infrastructure/template.yaml
BUILD_DIR:= .aws-sam/build
PARAMETERS_FILE:= parameters.json
S3_BUCKET:= ticket-grooming-automation-artifacts
LAYERS_DIR:= layers
REQUIREMENTS_FILE:= src/layers/requirements.txt
JQL_QUERY := $(shell jq -r '.DefaultJqlQuery' parameters.json | sed 's/"/\\"/g' | sed 's/ /\\ /g')

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
	--no-progressbar

.PHONY: deploy
deploy:
	@echo "Deploying AWS SAM application..."
	@echo "Using DefaultJqlQuery: '$$JQL_QUERY'"
	sam deploy --template-file $(BUILD_DIR)/packaged.yaml \
	--stack-name $(STACK_NAME) \
	--region $(REGION) \
	--capabilities CAPABILITY_IAM \
	--parameter-overrides \
	JiraApiUser="$$(jq -r '.JiraApiUser' $(PARAMETERS_FILE))" \
	JiraApiToken="$$(jq -r '.JiraApiToken' $(PARAMETERS_FILE))" \
	JiraBaseUrl="$$(jq -r '.JiraBaseUrl' $(PARAMETERS_FILE))" \
	BedrockEndpoint="$$(jq -r '.BedrockEndpoint' $(PARAMETERS_FILE))" \
	DefaultJqlQuery="$(JQL_QUERY)"

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

.PHONY: create-agent-alias update-lambda
create-agent-alias:
	@echo "Checking if stack exists..."; \
	if ! aws cloudformation describe-stacks --stack-name $(STACK_NAME) --region $(REGION) > /dev/null 2>&1; then \
		echo "Stack $(STACK_NAME) does not exist. Would you like to deploy it first? (y/n)"; \
		read response; \
		if [ "$$response" = "y" ]; then \
			echo "Deploying stack..."; \
			$(MAKE) build package deploy; \
		else \
			echo "Aborting"; \
			exit 1; \
		fi; \
	else \
		echo "Stack exists, updating lambda function"; \
	fi
	# $(eval AGENT_ID := $(shell aws cloudformation describe-stacks --stack-name $(STACK_NAME) --region $(REGION) --query "Stacks[0].Outputs[?OutputKey=='ManagerAssistantAgentId'].OutputValue" --output text))
	@if [ -z "$(AGENT_ID)" ]; then \
		echo "Could not find agent ID in stack outputs. Trying to get resource ID directly..."; \
		AGENT_ID=$$(aws cloudformation describe-stack-resource --stack-name $(STACK_NAME) --logical-resource-id ManagerAssistantAgent --query "StackResourceDetail.PhysicalResourceId" --output text); \
	fi
	@echo "Found agent ID: $(AGENT_ID)"
	@echo "Creating a new agent version..."
	# $(eval VERSION_ID := $(shell aws bedrock create-agent-version --agent-id $(AGENT_ID) --agent-version-name "v1-$$(date +%Y%m%d%H%M%S)" --description "Version created on $$(date)" --query "agentVersion.agentVersionId" --output text))
	# @echo "New agent version created: $(VERSION_ID)"
# Update the Lambda function with the agent alias
update-lambda:
	@if [ -z "$(AGENT_ID)" ] || [ -z "$(ALIAS_ID)" ]; then \
		echo "ERROR: AGENT_ID and ALIAS_ID must be provided"; \
		exit 1; \
	fi
	
	@echo "Updating Lambda function with agent ID $(AGENT_ID) and alias ID $(ALIAS_ID)..."
	$(eval FUNCTION_NAME := $(shell aws cloudformation describe-stack-resource --stack-name $(STACK_NAME) --logical-resource-id AnalyzeTicketsFunction --query "StackResourceDetail.PhysicalResourceId" --output text))
	
	@echo "Updating function: $(FUNCTION_NAME)"
	aws lambda update-function-configuration \
		--function-name $(FUNCTION_NAME) \
		--environment "Variables={AGENT_ID=$(AGENT_ID),AGENT_ALIAS_ID=$(ALIAS_ID),BEDROCK_ENDPOINT=bedrock-agent-runtime.${REGION}.amazonaws.com,DEFAULT_JQL_QUERY=project=PROJ+AND+status=Open+ORDER+BY+priority+DESC}"
	
	@echo "Lambda function updated successfully!"

# Example usage:
# 1. make create-agent-alias
# 2. make update-lambda AGENT_ID=<agent_id> ALIAS_ID=<alias_id>
