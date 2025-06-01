import boto3
import os

s3 = boto3.client('s3')

def upload_file_to_s3(file_path, bucket_name, s3_key=None):
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if s3_key is None:
        s3_key = os.path.basename(file_path)

    try:
        print(f"Uploading {file_path} to s3://{bucket_name}/{s3_key} ...")
        s3.upload_file(file_path, bucket_name, s3_key)
        print("Upload successful.")
    except Exception as e:
        print(f"Upload failed: {str(e)}")

if __name__ == "__main__":
    file_path = "robot_code.zip"           
    bucket_name = "robot-code-bucket" 
    s3_key = "uploads/robot_code.zip"    

    upload_file_to_s3(file_path, bucket_name, s3_key)
