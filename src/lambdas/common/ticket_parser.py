from typing import Dict, List, Any
from jira import Issue


def parse_ticket(issue: Issue) -> Dict[str, Any]:
    """
    Parse a single Jira issue into a dictionary with key information.
    
    Args:
        issue (Issue): A Jira issue object
        
    Returns:
        Dict[str, Any]: Dictionary containing parsed ticket information
    """
    return {
        "id": issue.key,
        "title": issue.fields.summary,
        "description": issue.fields.description,
        "comments": [
            {
                "author": comment.author.displayName,
                "body": comment.body,
                "created": comment.created
            }
            for comment in issue.fields.comment.comments
        ]
    }


def parse_tickets(issues: List[Issue]) -> List[Dict[str, Any]]:
    """
    Parse a list of Jira issues into a list of dictionaries.
    
    Args:
        issues (List[Issue]): List of Jira issue objects
        
    Returns:
        List[Dict[str, Any]]: List of dictionaries containing parsed ticket information
    """
    return [parse_ticket(issue) for issue in issues]


def parse_ticket_from_dict(ticket: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a ticket from a dictionary (useful for tickets fetched via REST API).
    
    Args:
        ticket (Dict[str, Any]): Dictionary containing ticket information
        
    Returns:
        Dict[str, Any]: Dictionary containing parsed ticket information
    """
    fields = ticket.get('fields', {})
    comments = fields.get('comment', {}).get('comments', [])
    
    return {
        "key": ticket.get('key'),
        "summary": fields.get('summary'),
        "description": fields.get('description'),
        "status": fields.get('status', {}).get('name'),
        "comments": [
            {
                "author": comment.get('author', {}).get('displayName'),
                "body": comment.get('body'),
                "created": comment.get('created')
            }
            for comment in comments
        ]
    }


def parse_tickets_from_dict(tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Parse a list of tickets from dictionaries (useful for tickets fetched via REST API).
    
    Args:
        tickets (List[Dict[str, Any]]): List of dictionaries containing ticket information
        
    Returns:
        List[Dict[str, Any]]: List of dictionaries containing parsed ticket information
    """
    return [parse_ticket_from_dict(ticket) for ticket in tickets] 