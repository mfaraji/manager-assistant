# Ticket Grooming Automation

A serverless application that automates the process of analyzing and grooming Jira tickets using AWS Bedrock and Claude AI.

## Overview

This project leverages AWS Bedrock Agents and Lambda functions to automatically analyze Jira tickets, identify issues with ticket quality, and provide suggestions for improvement. The system runs on a scheduled basis to help maintain high-quality tickets in your Jira backlog.

## Architecture

![Architecture Diagram](docs/architecture.png)

The application consists of:

- **AWS Bedrock Agent** - Powered by Claude 3.5 Sonnet, analyzes tickets and generates improvement suggestions
- **Lambda Functions**:
  - `FetchTicketsFunction` - Retrieves ticket data from Jira
  - `AnalyzeTicketsFunction` - Sends tickets to Bedrock for analysis
  - `UpdateJiraFunction` - Updates tickets with AI suggestions
- **EventBridge Rule** - Schedules regular execution
- **Secrets Manager** - Securely stores Jira credentials

## Prerequisites

- AWS CLI installed and configured
- AWS SAM CLI
- Python 3.9+
- Jira account with API access
- AWS Bedrock access with Claude 3.5 Sonnet permissions

## Setup

1. Clone this repository
2. Create a `parameters.json` file with your configuration:

```json
{
  "JiraApiUser": "your-jira-email@example.com",
  "JiraApiToken": "your-jira-api-token",
  "JiraBaseUrl": "https://your-domain.atlassian.net",
  "BedrockEndpoint": "bedrock.us-east-1.amazonaws.com"
}
```

3. Deploy the application:

```bash
make clean
make build
make package
make deploy
```

## Usage

The application runs automatically on the schedule defined in the `GroomingEventRule` (default: every 14 days). It will:

1. Fetch tickets from Jira based on your configured JQL query
2. Analyze ticket content using Claude AI
3. Provide suggestions for improving ticket clarity, completeness, and actionability

You can also invoke the process manually through the AWS Console or CLI.

## Development

### Project Structure

```
.
├── infrastructure/          # CloudFormation templates
├── layers/                  # Lambda layer dependencies
├── src/
│   ├── lambdas/             # Lambda function code
│   └── layers/              # Layer requirements
├── parameters.json          # Configuration parameters
├── Makefile                 # Build and deployment commands
└── README.md                # This file
```

### Extending the Project

To modify the criteria used for ticket analysis:
1. Update the agent instruction in `template.yaml`
2. Adjust the Lambda functions as needed
3. Redeploy using `make deploy`

### Testing

Test your changes before deployment:

```bash
make validate      # Validate CloudFormation template
make build         # Build the application
```

## Troubleshooting

- **Deployment Errors**: Check your AWS credentials and confirm you have the necessary permissions
- **Lambda Execution Issues**: View CloudWatch logs for the specific Lambda function
- **Jira API Errors**: Verify your Jira credentials and API token

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 