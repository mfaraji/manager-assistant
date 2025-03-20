import boto3
import json
import os
from typing import Dict, Any
from jira import JIRA


def get_jira_credentials() -> Dict[str, Any]:
    """
    Fetch Jira credentials from AWS Secrets Manager.
    
    Returns:
        Dict[str, Any]: Dictionary containing Jira credentials
    """
    secret_name = os.environ.get("JIRA_SECRET_NAME", "jiraCredentials")
    region_name = os.environ.get("AWS_REGION", "us-east-1")

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name="secretsmanager", region_name=region_name)

    try:
        # Retrieve the secret value
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name)
        secret = get_secret_value_response["SecretString"]
        return json.loads(secret)
    except Exception as e:
        print(f"Error retrieving secret: {e}")
        raise


def get_jira_client() -> JIRA:
    """
    Create and return a Jira client using credentials from Secrets Manager.
    
    Returns:
        JIRA: Configured Jira client instance
    """
    credentials = get_jira_credentials()
    
    return JIRA(
        server=credentials['jira_base_url'],
        basic_auth=(credentials['jira_api_user'], credentials['jira_api_token'])
    ) 