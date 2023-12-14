import boto3
import os
import logging
import json
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def delete_empty_groups(iam_client, sns_topic_arn):
    deleted_groups = []

    try:
        groups = iam_client.list_groups()['Groups']

        for group in groups:
            group_name = group['GroupName']
            users = iam_client.get_group(GroupName=group_name)['Users']

            if not users:
                # Detach all policies attached to the group
                attached_policies = iam_client.list_attached_group_policies(GroupName=group_name)['AttachedPolicies']
                for policy in attached_policies:
                    iam_client.detach_group_policy(GroupName=group_name, PolicyArn=policy['PolicyArn'])
                    logger.info(f"Detached policy {policy['PolicyName']} from group {group_name}")

                # Now delete the group
                iam_client.delete_group(GroupName=group_name)
                logger.info(f"Deleted empty group {group_name}")

                deleted_groups.append(group_name)

        if deleted_groups:
            sns_client = boto3.client('sns')
            message = f"Deleted the following empty IAM groups: {', '.join(deleted_groups)}"
            sns_client.publish(TopicArn=sns_topic_arn, Message=message)
            logger.info("Sent consolidated message to SNS topic.")
        
    except ClientError as e:
        logger.error(f"An error occurred: {e}")
        raise e

def lambda_handler(event, context):
    iam_client = boto3.client('iam')
    sns_topic_arn = os.environ['SNS_TOPIC_ARN']
    delete_empty_groups(iam_client, sns_topic_arn)

    return {
        'statusCode': 200,
        'body': json.dumps('Successfully processed IAM groups.')
    }
