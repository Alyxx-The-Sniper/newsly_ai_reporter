# app/storage.py
import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from .config import settings

region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
endpoint = os.getenv("S3_ENDPOINT")  # optional for S3-compatible services

s3 = boto3.client("s3", region_name=region, endpoint_url=endpoint) if region or endpoint else boto3.client("s3")

def upload_to_s3(file_path: str, key: str) -> str:
    bucket = settings.s3_bucket
    if not bucket:
        return "S3_BUCKET not set – skipping upload"
    try:
        # No ACL param -> compatible with buckets that enforce bucket-owner ownership
        s3.upload_file(file_path, bucket, key)
        return f"https://{bucket}.s3.amazonaws.com/{key}"
    except NoCredentialsError:
        return "AWS credentials not found – skipping upload"
    except ClientError as e:
        return f"S3 error: {e}"
    

# def presign_url(key: str, expires: int = 3600) -> str:
#     """Create a temporary HTTPS link to a private object."""
#     bucket = settings.s3_bucket
#     if not bucket:
#         return ""
#     try:
#         return s3.generate_presigned_url(
#             "get_object",
#             Params={"Bucket": bucket, "Key": key},
#             ExpiresIn=expires,
#         )
#     except ClientError as e:
#         code = e.response.get("Error", {}).get("Code", "")
#         return f"Presign error: {code}"
