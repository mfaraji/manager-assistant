def lambda_handler(event, context):
    """
    A dummy AWS Lambda function that does nothing.
    """
    print("This is a dummy Lambda function. It does nothing.")

    # Return a basic response
    return {
        "statusCode": 200,
        "body": "Dummy Lambda executed successfully!"
    }
