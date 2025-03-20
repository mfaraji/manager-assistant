import json
import os
from typing import Dict, Any, List
from common.ticket_parser import parse_tickets
from common.jira_client import get_jira_client


def get_bedrock_client():
    """Create and return a Bedrock client."""
    import boto3
    return boto3.client('bedrock-runtime')


def analyze_ticket_with_bedrock(bedrock_client, agent_id: str, ticket: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze a ticket using the Bedrock agent.
    
    Args:
        bedrock_client: Bedrock client instance
        agent_id (str): ID of the Bedrock agent
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
    
    # Call the Bedrock agent
    response = bedrock_client.invoke_agent(
        agentId=agent_id,
        inputText=prompt
    )
    
    return {
        'ticket_key': ticket['key'],
        'analysis': response['completion']
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to analyze tickets using Bedrock.
    
    Args:
        event (Dict[str, Any]): Event containing list of ticket keys
        context (Any): Lambda context
        
    Returns:
        Dict[str, Any]: Response containing analysis results
    """
    try:
        # Get ticket keys from the event
        ticket_keys = event.get('ticket_keys', [])
        if not ticket_keys:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No ticket keys provided'})
            }
        
        # Get agent ID from environment
        agent_id = os.environ.get('AGENT_ID')
        if not agent_id:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'AGENT_ID environment variable not set'})
            }
        
        # Initialize clients
        jira = get_jira_client()
        bedrock = get_bedrock_client()
        
        # Fetch and parse tickets
        issues = [jira.issue(key) for key in ticket_keys]
        parsed_tickets = parse_tickets(issues)
        
        # Analyze each ticket
        analysis_results = []
        for ticket in parsed_tickets:
            result = analyze_ticket_with_bedrock(bedrock, agent_id, ticket)
            analysis_results.append(result)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'analyses': analysis_results,
                'count': len(analysis_results)
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
