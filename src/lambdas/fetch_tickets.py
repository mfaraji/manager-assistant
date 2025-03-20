import json
from typing import Dict, Any
from common.ticket_parser import parse_tickets
from common.jira_client import get_jira_client


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to fetch ticket details from Jira.
    
    Args:
        event (Dict[str, Any]): Event containing list of ticket IDs
        context (Any): Lambda context
        
    Returns:
        Dict[str, Any]: Response containing fetched ticket details
    """
    try:
        # Get ticket IDs from the event payload
        payload = json.loads(event.get('Payload', '{}'))
        ticket_ids = payload.get('ticketIds', [])
        
        if not ticket_ids:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No ticket IDs provided'})
            }
        
        # Initialize Jira client
        jira = get_jira_client()
        
        # Fetch tickets from Jira
        issues = [jira.issue(key) for key in ticket_ids]
        
        # Parse tickets using common parser
        parsed_tickets = parse_tickets(issues)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'tickets': parsed_tickets
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
