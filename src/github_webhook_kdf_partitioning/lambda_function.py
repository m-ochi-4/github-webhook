
from base64 import b64decode, b64encode
from datetime import datetime, timezone
from json import loads, dumps


def _conv(record: dict) -> dict:

    payload = loads(b64decode(record["data"]))

    # Do custom processing on the payload here
    timestamp = datetime.fromtimestamp(record["approximateArrivalTimestamp"] / 1000, timezone.utc)

    return {
        "recordId": record["recordId"],
        "result": "Ok",
        "data": b64encode(dumps(payload, ensure_ascii=False, separators=(",", ":"), indent=None).encode("utf-8") + b"\n").decode("utf-8"),
        "metadata": {
            "partitionKeys": {
                "year": timestamp.strftime("%Y"),
                "month": timestamp.strftime("%m"),
                "day": timestamp.strftime("%d"),
                "hour": timestamp.strftime("%H"),
            },
        },
    }


def lambda_handler(event, context) -> dict[str, list[dict]]:
    return {"records": [_conv(record) for record in event["records"]]}
