
import hashlib
import hmac
from base64 import b64decode

import boto3


_SSM_AWS_REGION = "us-east-1"
_SSM_PARAM_NAME_GITHUB_WEBHOOK_SECRET_TOKEN = "/github/webhook/secret-token/default"
_SSM_PARAM_NAME_GITHUB_WEBHOOK_APIGW_APIKEY = "/github/webhook/apigw-apikey/default"

_ssm_client = boto3.client("ssm", region_name=_SSM_AWS_REGION)
_GITHUB_WEBHOOK_SECRET_TOKEN = _ssm_client.get_parameter(Name=_SSM_PARAM_NAME_GITHUB_WEBHOOK_SECRET_TOKEN, WithDecryption=True)["Parameter"]["Value"].encode("utf-8")  # pyright: ignore[reportTypedDictNotRequiredAccess]
_GITHUB_WEBHOOK_APIGW_APIKEY = _ssm_client.get_parameter(Name=_SSM_PARAM_NAME_GITHUB_WEBHOOK_APIGW_APIKEY, WithDecryption=True)["Parameter"]["Value"]  # pyright: ignore[reportTypedDictNotRequiredAccess]
_CF_HEADER_X_API_KEY = [{"key": "X-API-Key", "value": _GITHUB_WEBHOOK_APIGW_APIKEY}]


def verify_signature(payload_body: bytes, secret_token: bytes, signature_header: str) -> bool:

    hash_object = hmac.new(secret_token, msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()

    return hmac.compare_digest(expected_signature, signature_header)


def lambda_handler(event, context):

    request = event["Records"][0]["cf"]["request"]
    header_signature = request["headers"].get("x-hub-signature-256")

    if header_signature and request["method"] == "POST" and \
            verify_signature(b64decode(request["body"]["data"]), _GITHUB_WEBHOOK_SECRET_TOKEN, header_signature[0]["value"]):

        request["headers"]["x-api-key"] = _CF_HEADER_X_API_KEY
        return request

    return {"status": "403"}
