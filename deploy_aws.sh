#!/bin/bash
# deploy_aws.sh: Deploys tg-reader scheduled Lambda, S3 bucket, and SES setup
# Prerequisites: AWS CLI configured, jq, zip, Python 3.12 runtime compatible

set -euo pipefail

# === CONFIGURATION ===
LAMBDA_NAME="tg-reader-scheduled"
S3_BUCKET="tg-reader-$(uuidgen | cut -d'-' -f1)"
LAMBDA_ROLE_NAME="tg-reader-lambda-role"
LAMBDA_ZIP="lambda_package.zip"
LAMBDA_HANDLER="scheduled_tg.lambda_handler"
REGION="eu-west-1"
SES_EMAIL="cichymail@gmail.com"  # Must be a verified SES sender

# === ARGUMENT PARSING ===
if [[ "$1" == "install" ]]; then
  echo "[tg-reader] Full install (all resources)"
  DO_INSTALL=1
  DO_REDEPLOY=1
elif [[ "$1" == "redeploy" ]]; then
  echo "[tg-reader] Redeploy Lambda code only"
  DO_INSTALL=0
  DO_REDEPLOY=1
else
  echo "Usage: $0 [install|redeploy]"
  exit 1
fi

if [[ "$DO_INSTALL" == "1" ]]; then
# === 1. Create S3 bucket ===
echo "Creating S3 bucket: $S3_BUCKET"
aws s3api create-bucket --bucket "$S3_BUCKET" --region "$REGION" --create-bucket-configuration LocationConstraint="$REGION"

# === 2. Create IAM role for Lambda ===
echo "Creating IAM role: $LAMBDA_ROLE_NAME"
cat > trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
aws iam create-role --role-name "$LAMBDA_ROLE_NAME" --assume-role-policy-document file://trust-policy.json || true

# Attach policies for S3, SES, and Lambda logging
echo "Attaching policies to role"
aws iam attach-role-policy --role-name "$LAMBDA_ROLE_NAME" --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
aws iam attach-role-policy --role-name "$LAMBDA_ROLE_NAME" --policy-arn arn:aws:iam::aws:policy/AmazonSESFullAccess
aws iam attach-role-policy --role-name "$LAMBDA_ROLE_NAME" --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Wait for role propagation
sleep 10
ROLE_ARN=$(aws iam get-role --role-name "$LAMBDA_ROLE_NAME" --query 'Role.Arn' --output text)

# === 3. Verify SES sender email ===
echo "Verifying SES sender email: $SES_EMAIL"
aws ses verify-email-identity --email-address "$SES_EMAIL" --region "$REGION" || true

echo "Please check $SES_EMAIL and click the verification link from AWS SES before continuing."
read -p "Press Enter after verifying the SES email address..."
fi

# === 4. Package Lambda code with dependencies ===
echo "Packaging Lambda function with dependencies..."
rm -rf lambda_build "$LAMBDA_ZIP"
mkdir lambda_build
pip install -r install.txt -t lambda_build
cp -r *.py config.json scheduled.json lambda_build/
cd lambda_build
zip -r ../"$LAMBDA_ZIP" .
cd ..

# === 5. Create or update Lambda function ===
if [[ "$DO_INSTALL" == "1" ]]; then
  echo "Creating Lambda function: $LAMBDA_NAME"
  aws lambda create-function \
    --function-name "$LAMBDA_NAME" \
    --runtime python3.12 \
    --role "$ROLE_ARN" \
    --handler "$LAMBDA_HANDLER" \
    --timeout 900 \
    --memory-size 1024 \
    --zip-file fileb://"$LAMBDA_ZIP" \
    --region "$REGION" || \
  aws lambda update-function-code --function-name "$LAMBDA_NAME" --zip-file fileb://"$LAMBDA_ZIP" --region "$REGION"
else
  echo "Updating Lambda code only: $LAMBDA_NAME"
  aws lambda update-function-code --function-name "$LAMBDA_NAME" --zip-file fileb://"$LAMBDA_ZIP" --region "$REGION"
fi

if [[ "$DO_INSTALL" == "1" ]]; then
  # === 6. Wait for Lambda to become active, then add environment variables ===
  echo "Waiting for Lambda function to become active..."
  aws lambda wait function-active --function-name "$LAMBDA_NAME" --region "$REGION"
  echo "Configuring Lambda environment variables..."
  aws lambda update-function-configuration \
    --function-name "$LAMBDA_NAME" \
    --environment "Variables={S3_BUCKET=$S3_BUCKET,SES_SENDER=$SES_EMAIL,REGION=$REGION}" \
    --region "$REGION"

  # === 7. Schedule Lambda with EventBridge ===
  echo "Creating EventBridge rule for scheduled Lambda..."
  RULE_NAME="tg-reader-schedule"
  SCHEDULE="cron(0 4 * * ? *)"  # Change as needed
  aws events put-rule --name "$RULE_NAME" --schedule-expression "$SCHEDULE" --region "$REGION"
  LAMBDA_ARN=$(aws lambda get-function --function-name "$LAMBDA_NAME" --query 'Configuration.FunctionArn' --output text)
  aws events put-targets --rule "$RULE_NAME" --targets "Id=1,Arn=$LAMBDA_ARN" --region "$REGION"
  aws lambda add-permission --function-name "$LAMBDA_NAME" --statement-id eventbridge-invoke --action 'lambda:InvokeFunction' --principal events.amazonaws.com --source-arn arn:aws:events:$REGION:$(aws sts get-caller-identity --query Account --output text):rule/$RULE_NAME --region "$REGION" || true

  echo "Deployment complete!"
  echo "S3 bucket: $S3_BUCKET"
  echo "Lambda function: $LAMBDA_NAME"
  echo "SES sender: $SES_EMAIL (must be verified)"
  echo "EventBridge rule: $RULE_NAME (schedule: $SCHEDULE)"
else
  echo "Lambda code redeployed."
fi
