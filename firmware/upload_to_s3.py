import argparse
import os
import sys

try:
    import boto3
    from botocore.exceptions import NoCredentialsError, ClientError
except ImportError:
    print("[ERROR] boto3 not installed. Run: pip install boto3")
    sys.exit(1)


def get_s3_client():
    """
    Create an S3 client using credentials from environment variables.

    Credentials are never hardcoded. boto3 automatically reads
    AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY from environment
    variables if present.

    Returns:
        boto3 S3 client object
    """
    region = os.environ.get("AWS_REGION", "ap-south-1")
    return boto3.client("s3", region_name=region)


def upload_file(s3_client, local_path: str, bucket: str, s3_key: str) -> bool:
    """
    Upload a single file to S3.

    Args:
        s3_client: boto3 S3 client
        local_path: path to local file to upload
        bucket: S3 bucket name
        s3_key: destination path within the bucket

    Returns:
        bool: True if upload succeeded, False otherwise
    """
    if not os.path.exists(local_path):
        print(f"[ERROR] File not found: {local_path}")
        return False

    try:
        s3_client.upload_file(local_path, bucket, s3_key)
        size_kb = os.path.getsize(local_path) / 1024
        print(f"[+] Uploaded: {local_path} -> s3://{bucket}/{s3_key} ({size_kb:.1f} KB)")
        return True
    except NoCredentialsError:
        print("[ERROR] AWS credentials not found")
        print("[ERROR] Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
        return False
    except ClientError as e:
        print(f"[ERROR] Upload failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Upload signed firmware artifacts to S3"
    )
    parser.add_argument(
        "--version",
        type=str,
        required=True,
        help="Firmware version e.g. 1.0.0"
    )
    parser.add_argument(
        "--firmware",
        type=str,
        required=True,
        help="Path to firmware binary (.bin)"
    )
    parser.add_argument(
        "--signature",
        type=str,
        required=True,
        help="Path to signature file (.sig)"
    )
    parser.add_argument(
        "--manifest",
        type=str,
        required=True,
        help="Path to manifest.json"
    )
    parser.add_argument(
        "--bucket",
        type=str,
        default=None,
        help="S3 bucket name (default: reads S3_BUCKET_NAME env var)"
    )

    args = parser.parse_args()

    # Resolve bucket name
    bucket = args.bucket or os.environ.get("S3_BUCKET_NAME")
    if not bucket:
        print("[ERROR] S3 bucket name not provided")
        print("[ERROR] Use --bucket argument or set S3_BUCKET_NAME env var")
        sys.exit(1)

    print(f"[*] Uploading firmware v{args.version} to s3://{bucket}/releases/{args.version}/")
    print()

    s3_client = get_s3_client()

    files_to_upload = [
        (args.firmware, f"releases/{args.version}/{os.path.basename(args.firmware)}"),
        (args.signature, f"releases/{args.version}/{os.path.basename(args.signature)}"),
        (args.manifest, f"releases/{args.version}/{os.path.basename(args.manifest)}"),
    ]

    success_count = 0
    for local_path, s3_key in files_to_upload:
        if upload_file(s3_client, local_path, bucket, s3_key):
            success_count += 1

    print()
    if success_count == len(files_to_upload):
        print(f"[+] All {success_count} files uploaded successfully")
        print(f"[+] S3 path: s3://{bucket}/releases/{args.version}/")
    else:
        print(f"[ERROR] Only {success_count}/{len(files_to_upload)} files uploaded")
        sys.exit(1)


if __name__ == "__main__":
    main()