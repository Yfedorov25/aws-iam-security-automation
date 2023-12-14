import boto3
import os
import logging
import datetime
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    sns_topic_arn = os.environ['SNS_TOPIC_ARN']
    sns = boto3.client('sns')
    iam = boto3.client('iam')

    users = iam.list_users()['Users']
    for user in users:
        username = user['UserName']
        access_keys = iam.list_access_keys(UserName=username)['AccessKeyMetadata']

        for access_key in access_keys:
            access_key_id = access_key['AccessKeyId']
            try:
                last_used_info = iam.get_access_key_last_used(AccessKeyId=access_key_id)['AccessKeyLastUsed']
                last_used_date = last_used_info.get('LastUsedDate')
                if last_used_date:
                    age = (datetime.datetime.utcnow() - last_used_date.replace(tzinfo=None)).days
                    logger.info(f"Access key {access_key_id} is {age} days old for user {username}.")
                    if age > 30:
                        handle_old_access_key(iam, sns, username, access_key_id, sns_topic_arn)
            except ClientError as e:
                logger.error(f"Error fetching last used date for access key {access_key_id}: {e}")
                continue

def handle_old_access_key(iam, sns, username, access_key_id, sns_topic_arn):
    iam.update_access_key(UserName=username, AccessKeyId=access_key_id, Status='Inactive')
    iam.delete_access_key(UserName=username, AccessKeyId=access_key_id)
    logger.info(f"Access key {access_key_id} for user {username} has been deactivated and deleted.")

    new_access_key = iam.create_access_key(UserName=username)
    new_access_key_id = new_access_key['AccessKey']['AccessKeyId']
    logger.info(f"New access key {new_access_key_id} created for user {username} but not activated.")

    message = f"User {username} had an old access key {access_key_id} deactivated and deleted. A new access key {new_access_key_id} has been created but requires manual activation."
    sns.publish(TopicArn=sns_topic_arn, Message=message)
    logger.info("Notification sent to SNS topic.")

if __name__ == "__main__":
    lambda_handler(None, None)
