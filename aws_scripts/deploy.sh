#!/bin/bash

# === CONFIGURATION ===
STACK_NAME="s3-lambda-dynamodb-stack"
TEMPLATE_FILE="cloudformation.yaml"
LAMBDA_CODE="lambda_handler.py"
ZIP_FILE="lambda_code.zip"
S3_CODE_BUCKET="robot-code-bucket"   # Replace with your actual S3 bucket for Lambda code
S3_CODE_KEY="robot_code.zip"
REGION="us-east-1"                        # Change to your AWS region

# === STEP 1: Zip Lambda Code ===
echo "Zipping Lambda code..."
zip -r $ZIP_FILE $LAMBDA_CODE

# === STEP 2: Upload Lambda Code to S3 ===
echo "Uploading Lambda code to S3..."
aws s3 cp $ZIP_FILE s3://$S3_CODE_BUCKET/$S3_CODE_KEY --region $REGION

# === STEP 3: Deploy CloudFormation Stack ===
echo "Deploying CloudFormation stack..."
aws cloudformation deploy \
  --template-file $TEMPLATE_FILE \
  --stack-name $STACK_NAME \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $REGION

# === STEP 4: Output Deployment Results ===
echo "Fetching stack outputs..."
aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query "Stacks[0].Outputs" \
  --output table

echo "✅ Deployment complete."
