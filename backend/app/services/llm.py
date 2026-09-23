"""Claude via AWS Bedrock (Converse API).

boto3 authenticates to Bedrock with AWS_BEARER_TOKEN_BEDROCK from the environment.
The model id comes from settings (CLAUDE_MODEL). This module only sends text and
returns text; it never interprets numbers.
"""
import boto3

from app.config import settings

_client = boto3.client("bedrock-runtime", region_name=settings.aws_region)


def invoke(prompt: str, max_tokens: int = 1000) -> str:
    response = _client.converse(
        modelId=settings.claude_model,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": 0},
    )
    return response["output"]["message"]["content"][0]["text"]
