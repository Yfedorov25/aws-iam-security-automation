import boto3
import os
import logging
import string
import random
from datetime import datetime, timezone, timedelta
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)

def generate_password(length=12):
    """
    Generates a random password.
    """
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(length))
    return password

def update_secret_for_user(secrets_manager_client, username, new_password):
    """
    Update or create a secret for the user in AWS Secrets Manager.
    """
    secret_name = f"iam_user_{username}_password"
    try:
        secrets_manager_client.get_secret_value(SecretId=secret_name)
        secrets_manager_client.put_secret_value(SecretId=secret_name, SecretString=new_password)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            secrets_manager_client.create_secret(Name=secret_name, SecretString=new_password)
        else:
            logging.error(f"Error handling secret for {username}: {e}")
            raise e

def lambda_handler(event, context):
    sns_topic_arn = os.environ['SNS_TOPIC_ARN']
    iam = boto3.client('iam')
    sns = boto3.client('sns')
    secrets_manager_client = boto3.client('secretsmanager')
    today = datetime.now(timezone.utc)

    users = iam.list_users()['Users']
    updated_users = []

    for user in users:
        username = user['UserName']

        try:
            # Check if the user has a password last used date
            user_details = iam.get_user(UserName=username)
            last_password_use = user_details['User'].get('PasswordLastUsed')
            if last_password_use:
                password_age_days = (today - last_password_use).total_seconds() / (3600 * 24)  # Convert seconds to days

                if password_age_days > 90:
                    new_password = generate_password()
                    iam.update_login_profile(UserName=username, Password=new_password, PasswordResetRequired=False)
                    logging.info(f"Password updated for user {username}")

                    update_secret_for_user(secrets_manager_client, username, new_password)
                    logging.info(f"Password for user {username} stored in Secrets Manager")
                    updated_users.append(username)
            else:
                logging.info(f"No password last used date for user {username}, skipping.")
        except ClientError as e:
            logging.error(f"Error processing user {username}: {e}")

    # Send consolidated notification
    if updated_users:
        message = f"Passwords updated for the following users and stored in Secrets Manager: {', '.join(updated_users)}."
        sns.publish(TopicArn=sns_topic_arn, Message=message)
        logging.info("Consolidated notification sent.")

    return {'statusCode': 200, 'body': 'Process completed successfully.'}
