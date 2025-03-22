import json
import os
from typing import Dict, Any, List
from common.ticket_parser import parse_tickets
from common.jira_client import get_jira_client


def get_bedrock_clients():
    """Create and return Bedrock clients."""
    import boto3
    
    # Get the correct endpoint from environment variable
    endpoint_url = os.environ.get('BEDROCK_ENDPOINT')
    region = os.environ.get('AWS_REGION', 'us-east-1')
    
    # Check if we have a valid endpoint for runtime
    if not endpoint_url:
        endpoint_url = f"bedrock-runtime.{region}.amazonaws.com"
    
    # Make sure the endpoint has the proper format
    if not endpoint_url.startswith('https://'):
        endpoint_url = f"https://{endpoint_url}"
    
    print(f"Using Bedrock endpoint: {endpoint_url}")
    
    # Create specialized client for agent runtime
    agent_client = boto3.client('bedrock-agent-runtime', endpoint_url=endpoint_url)
    return agent_client


def analyze_ticket_with_bedrock(agent_client, agent_id: str, agent_alias_id: str, ticket: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze a ticket using the Bedrock agent.
    
    Args:
        agent_client: Bedrock agent runtime client
        agent_id (str): ID of the Bedrock agent
        agent_alias_id (str): Alias ID of the Bedrock agent
        ticket (Dict[str, Any]): Ticket to analyze
        
    Returns:
        Dict[str, Any]: Analysis results
    """
    # Prepare the prompt for the agent
    prompt = f"""
    Analyze the following Jira ticket and provide feedback:
    
    Key: {ticket['key']}
    Summary: {ticket['summary']}
    Description: {ticket['description']}
    Status: {ticket['status']}
    
    Comments:
    {json.dumps(ticket['comments'], indent=2)}
    
    Please provide:
    1. Clarity assessment
    2. Missing information
    3. Suggested improvements
    4. Action items
    """
    
    try:
        # Generate a unique session ID based on ticket key
        import uuid
        session_id = f"{ticket['key']}-{str(uuid.uuid4())}"
        
        # Call the Bedrock agent
        response = agent_client.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            inputText=prompt
        )
        
        # Process the streaming response
        full_response = ""
        
        # Handle the event stream response
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    # If bytes is already decoded to a string
                    if isinstance(chunk['bytes'], str):
                        full_response += chunk['bytes']
                    # If bytes is a binary object
                    else:
                        full_response += chunk['bytes'].decode('utf-8')
        
        return {
            'ticket_key': ticket['key'],
            'analysis': full_response if full_response else "No analysis provided"
        }
    except Exception as e:
        import traceback
        return {
            'ticket_key': ticket['key'],
            'analysis': f"Error analyzing ticket: {str(e)}",
            'traceback': traceback.format_exc()
        }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to analyze tickets using Bedrock.
    
    Args:
        event (Dict[str, Any]): Event containing JQL query
        context (Any): Lambda context
        
    Returns:
        Dict[str, Any]: Response containing analysis results
    """
    try:
        # Get JQL query from environment variable, or use event override if provided
        default_jql = os.environ.get('DEFAULT_JQL_QUERY', 'project=PROJ+AND+status=Open+ORDER+BY+priority+DESC')
        # Replace + with spaces for JIRA API
        default_jql = default_jql.replace('+', ' ')
        jql_query = event.get('jql_query', default_jql)
        
        # Get agent ID and alias ID from environment
        agent_id = os.environ.get('AGENT_ID')
        agent_alias_id = os.environ.get('AGENT_ALIAS_ID', 'TSTALIASID')
        
        if not agent_id:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'AGENT_ID environment variable not set'})
            }
        
        # Initialize clients
        jira = get_jira_client()
        agent_client = get_bedrock_client()
        
        # Log the parameters for debugging
        print(f"Using agent_id: {agent_id}")
        print(f"Using agent_alias_id: {agent_alias_id}")
        print(f"JQL query: {jql_query}")
        
        # Fetch issues based on JQL
        issues = jira.search_issues(jql_query, maxResults=10)  # Reduced for testing
        if not issues:
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'No tickets found matching the JQL query', 'jql_query': jql_query})
            }
            
        # Parse tickets
        parsed_tickets = parse_tickets(issues)
        
        # Analyze each ticket
        analysis_results = []
        for ticket in parsed_tickets:
            result = analyze_ticket_with_bedrock(agent_client, agent_id, agent_alias_id, ticket)
            analysis_results.append(result)
            # Add a small delay between requests to avoid rate limiting
            import time
            time.sleep(1)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'analyses': analysis_results,
                'count': len(analysis_results),
                'jql_query': jql_query
            }, default=str)  # Use default=str to handle any non-serializable objects
        }
        
    except Exception as e:
        import traceback
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'traceback': traceback.format_exc()
            })
        }
