import boto3
import os

# Initialize the S3 client
s3 = boto3.client('s3')

def upload_file_to_s3(file_path, bucket_name, s3_key=None):
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Use the filename as the S3 key if none provided
    if s3_key is None:
        s3_key = os.path.basename(file_path)

    try:
        print(f"Uploading {file_path} to s3://{bucket_name}/{s3_key} ...")
        s3.upload_file(file_path, bucket_name, s3_key)
        print("Upload successful.")
    except Exception as e:
        print(f"Upload failed: {str(e)}")

if __name__ == "__main__":
    # Example usage (replace these values with your own)
    file_path = "example.txt"           # File to upload
    bucket_name = "your-s3-bucket-name" # Target S3 bucket
    s3_key = "uploads/example.txt"      # Key (path in S3)

    upload_file_to_s3(file_path, bucket_name, s3_key)
