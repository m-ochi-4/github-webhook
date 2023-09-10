
import json
from os import environ

import boto3


_SNS_TOPIC_ARN = environ["SNS_TOPIC_ARN"]
_sns_client = boto3.client("sns")


def lambda_handler(event, context):

    message = event["Records"][0]["Sns"]["Message"]
    payload = json.loads(message)

    if (payload["headers"]["X-GitHub-Event"] == "repository" and
            payload["action"] in {"publicized", "created", } and
            payload.get("repository", {}).get("private") != True):

        _sns_client.publish(
            Message=message,
            TopicArn=_SNS_TOPIC_ARN,
            Subject=f"GitHub Publicized Repository Notification - {payload['repository']['full_name']}",
        )
