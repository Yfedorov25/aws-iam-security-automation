import boto3
import os
import json
from datetime import datetime
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    sns_topic_arn = os.environ['SNS_TOPIC_ARN']
    iam = boto3.client('iam')
    secrets_manager = boto3.client('secretsmanager')
    sns = boto3.client('sns')

    users = iam.list_users()['Users']
    messages = []

    for user in users:
        username = user['UserName']
        access_keys = iam.list_access_keys(UserName=username)['AccessKeyMetadata']

        for key in access_keys:
            key_id = key['AccessKeyId']
            key_status = key['Status']
            key_create_date = key['CreateDate']
            key_age = (datetime.now(key_create_date.tzinfo) - key_create_date).days

            if key_age > 90 and key_status == 'Active':
                iam.update_access_key(UserName=username, AccessKeyId=key_id, Status='Inactive')
                iam.delete_access_key(UserName=username, AccessKeyId=key_id)
                logger.info(f"Deactivated and deleted old access key for {username}")

                new_key = iam.create_access_key(UserName=username)['AccessKey']
                secret_name = f"{username}_access_key"
                secret_value = json.dumps({'AccessKeyId': new_key['AccessKeyId'], 'SecretAccessKey': new_key['SecretAccessKey']})

                try:
                    secrets_manager.create_secret(Name=secret_name, SecretString=secret_value)
                    logger.info(f"New access key stored in Secrets Manager for {username}")
                except ClientError as error:
                    logger.error(f"Error storing secret for {username}: {error}")

                user_message = f"User {username} had an old access key {key_id} removed. A new key has been created and stored in Secrets Manager."
                messages.append(user_message)

    if messages:
        consolidated_message = "\n".join(messages)
        sns.publish(TopicArn=sns_topic_arn, Message=consolidated_message)
        logger.info("Consolidated notification sent to SNS topic.")

    return {
        'statusCode': 200,
        'body': 'Access key rotation process completed.'
    }
