import boto3
import os
import logging
from datetime import datetime, timezone

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_aws_account_id():
    sts_client = boto3.client('sts')
    return sts_client.get_caller_identity()["Account"]

def analyze_access_advisor_for_user(iam_client, username, aws_account_id):
    service_last_accessed = {}

    try:
        user_policies = iam_client.list_attached_user_policies(UserName=username)['AttachedPolicies']
        if not user_policies:
            return "No permissions"

        response = iam_client.generate_service_last_accessed_details(Arn=f"arn:aws:iam::{aws_account_id}:user/{username}")
        job_id = response['JobId']

        while True:
            job_status = iam_client.get_service_last_accessed_details(JobId=job_id)
            if job_status['JobStatus'] in ['COMPLETED', 'FAILED']:
                break

        if job_status['JobStatus'] == 'COMPLETED':
            current_time = datetime.now(timezone.utc)
            unused_services = 0
            for service in job_status['ServicesLastAccessed']:
                last_authenticated = service.get('LastAuthenticated')
                if last_authenticated:
                    days_since_access = (current_time - last_authenticated).days
                    if days_since_access > 60:
                        service_last_accessed[service['ServiceNamespace']] = days_since_access
                else:
                    unused_services += 1

            if unused_services:
                service_last_accessed["unused_services_count"] = unused_services

        elif job_status['JobStatus'] == 'FAILED':
            logger.error(f"Failed to get service last accessed details for {username}")

    except iam_client.exceptions.NoSuchEntityException:
        return "No console access profile"

    except Exception as e:
        logger.error(f"Error processing user {username}: {e}")

    return service_last_accessed if service_last_accessed else "No unused services in the last 60 days"

def consolidate_findings(findings):
    message = "IAM User Permissions Analysis Report:\n\n"
    for username, services in findings.items():
        message += f"User: {username}\n"
        if isinstance(services, str):
            message += f"  - {services}\n"
        else:
            unused_services_count = services.pop("unused_services_count", 0)
            for service, days_since_access in services.items():
                message += f"  - {service} last accessed {days_since_access} days ago\n"
            if unused_services_count:
                message += f"  - {unused_services_count} services not accessed in the tracking period. Consider reviewing Access Advisor for potential permission pruning.\n"
        message += "\n"

    return message

def lambda_handler(event, context):
    sns_topic_arn = os.environ['SNS_TOPIC_ARN']
    iam_client = boto3.client('iam')
    sns_client = boto3.client('sns')
    aws_account_id = get_aws_account_id()

    findings = {}
    users = iam_client.list_users()['Users']
    for user in users:
        username = user['UserName']
        user_services = analyze_access_advisor_for_user(iam_client, username, aws_account_id)
        findings[username] = user_services

    consolidated_message = consolidate_findings(findings)
    sns_client.publish(TopicArn=sns_topic_arn, Message=consolidated_message)
    logger.info("Consolidated notification sent.")

    return {
        'statusCode': 200,
        'body': 'Completed analysis of IAM user permissions using Access Advisor.'
    }
