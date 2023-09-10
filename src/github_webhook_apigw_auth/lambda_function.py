
import json


def lambda_handler(event, context):
    print(json.dumps(event))
    print(context)
    return {
        "principalId": "*",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "execute-api:Invoke",
                    "Resource": event["methodArn"],
                }
            ]
        }
    }
