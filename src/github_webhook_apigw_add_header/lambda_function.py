
import json
from os import environ

import boto3


_SNS_TOPIC_ARN = environ["SNS_TOPIC_ARN"]
_sns_client = boto3.client("sns")


def lambda_handler(event, context):

    payload = json.loads(event["body"])
    payload["headers"] = {
        k: v
        for k, v in event["headers"].items()
        if k.startswith("X-GitHub-") or k.startswith("X-Hub-Signature")
    }

    _sns_client.publish(
        Message=json.dumps(payload, ensure_ascii=False, separators=(",", ":"), indent=None),
        TopicArn=_SNS_TOPIC_ARN,
    )

    return {
        "statusCode": 200,
        "body": "{}"
    }
