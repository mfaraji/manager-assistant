import json
import os
import logging
from typing import Dict, Any, List, Union
from common.jira_client import get_jira_client

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def add_comment_to_ticket(jira_client, ticket_key: str, comment_text: str) -> Dict[str, Any]:
    """
    Add a comment to a Jira ticket.
    
    Args:
        jira_client: Authenticated Jira client
        ticket_key (str): The key of the ticket (e.g., "PROJ-123")
        comment_text (str): The text of the comment to add
        
    Returns:
        Dict[str, Any]: Response containing status and comment details
    """
    try:
        # Add comment to the ticket
        logger.info(f"Adding comment to ticket {ticket_key}")
        comment = jira_client.add_comment(ticket_key, comment_text)
        
        return {
            "success": True,
            "ticket_key": ticket_key,
            "comment_id": comment.id,
            "message": f"Comment added successfully to ticket {ticket_key}"
        }
    except Exception as e:
        logger.error(f"Error adding comment to ticket {ticket_key}: {str(e)}")
        return {
            "success": False,
            "ticket_key": ticket_key,
            "error": str(e),
            "message": f"Failed to add comment to ticket {ticket_key}"
        }

def add_label_to_ticket(jira_client, ticket_key: str, labels: Union[str, List[str]]) -> Dict[str, Any]:
    """
    Add one or more labels to a Jira ticket.
    
    Args:
        jira_client: Authenticated Jira client
        ticket_key (str): The key of the ticket (e.g., "PROJ-123")
        labels (Union[str, List[str]]): Single label or list of labels to add
        
    Returns:
        Dict[str, Any]: Response containing status and label details
    """
    try:
        # Get the issue
        logger.info(f"Getting issue {ticket_key}")
        issue = jira_client.issue(ticket_key)
        
        # Convert single label to list if necessary
        if isinstance(labels, str):
            labels = [labels]
        
        # Get current labels
        current_labels = issue.fields.labels if hasattr(issue.fields, 'labels') else []
        logger.info(f"Current labels for {ticket_key}: {current_labels}")
        
        # Add new labels (avoid duplicates)
        new_labels = current_labels.copy()
        added_labels = []
        
        for label in labels:
            if label not in new_labels:
                new_labels.append(label)
                added_labels.append(label)
        
        # Update the issue with new labels
        if added_labels:
            logger.info(f"Adding labels to ticket {ticket_key}: {added_labels}")
            issue.update(fields={"labels": new_labels})
            
            return {
                "success": True,
                "ticket_key": ticket_key,
                "added_labels": added_labels,
                "all_labels": new_labels,
                "message": f"Labels {added_labels} added successfully to ticket {ticket_key}"
            }
        else:
            logger.info(f"No new labels to add to ticket {ticket_key}")
            return {
                "success": True,
                "ticket_key": ticket_key,
                "added_labels": [],
                "all_labels": current_labels,
                "message": f"No new labels were added to ticket {ticket_key} (labels already exist)"
            }
    except Exception as e:
        logger.error(f"Error adding labels to ticket {ticket_key}: {str(e)}")
        return {
            "success": False,
            "ticket_key": ticket_key,
            "error": str(e),
            "message": f"Failed to add labels to ticket {ticket_key}"
        }

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda function that updates Jira tickets based on actions.
    Supports two actions: comment and addLabel.
    
    Args:
        event (Dict[str, Any]): Event containing action and data
        context (Any): Lambda context
        
    Returns:
        Dict[str, Any]: Response containing the result of the action
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract action and data from the event
        action = event.get('action')
        data = event.get('data', {})
        
        if not action:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "success": False,
                    "error": "No action specified",
                    "message": "Please specify an action: 'comment' or 'addLabel'"
                })
            }
        
        # Get the Jira client
        jira_client = get_jira_client()
        
        # Process based on action
        if action.lower() == 'comment':
            # Validate required fields
            ticket_key = data.get('ticket_key')
            comment_text = data.get('comment')
            
            if not ticket_key or not comment_text:
                return {
                    "statusCode": 400,
                    "body": json.dumps({
                        "success": False,
                        "error": "Missing required fields",
                        "message": "For 'comment' action, 'ticket_key' and 'comment' fields are required"
                    })
                }
            
            result = add_comment_to_ticket(jira_client, ticket_key, comment_text)
            
        elif action.lower() == 'addlabel':
            # Validate required fields
            ticket_key = data.get('ticket_key')
            labels = data.get('labels')
            
            if not ticket_key or not labels:
                return {
                    "statusCode": 400,
                    "body": json.dumps({
                        "success": False,
                        "error": "Missing required fields",
                        "message": "For 'addLabel' action, 'ticket_key' and 'labels' fields are required"
                    })
                }
            
            result = add_label_to_ticket(jira_client, ticket_key, labels)
            
        else:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "success": False,
                    "error": f"Unsupported action: {action}",
                    "message": "Supported actions are: 'comment' and 'addLabel'"
                })
            }
        
        # Return the result
        return {
            "statusCode": 200 if result.get('success', False) else 500,
            "body": json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Error in lambda function: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "success": False,
                "error": str(e),
                "message": "Internal server error"
            })
        }
