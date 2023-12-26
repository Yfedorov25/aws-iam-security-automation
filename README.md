# AWS IAM Security Automation

## Overview
This repository contains a collection of AWS CloudFormation templates and Lambda functions designed to enhance IAM security and compliance within AWS environments. Each solution addresses a specific aspect of IAM security, from managing access keys to monitoring user activities.

## Table of Contents
- [Solutions Overview](#solutions-overview)
- [Usage Instructions](#usage-instructions)
- [Deployment Instructions](#deployment-instructions)
- [Solutions Description](#solutions-description)
- [Contributing](#contributing)


## Solutions Overview
The `aws-iam-security-automation` repository includes the following solutions:
- IAM User Activity Analysis and Removal of Unused Permissions
- Access Key Management
- Access Key Rotation
- Empty IAM Group Deletion
- IAM User Console Access Management

Each solution is stored in separate folders within the repository and includes a CloudFormation template and corresponding Lambda function code.

## Usage Instructions
To deploy these solutions:
1. Navigate to the desired solution's folder.
2. Review and update the CloudFormation template and Lambda function as needed.
3. Deploy the template using the AWS Management Console, AWS CLI, or your preferred deployment tool.

## Deployment Instructions

This repository is configured with a GitHub Actions workflow to automate the deployment of solutions. To utilize this automated deployment:

1. **Configure GitHub Secrets**:
    - Go to your GitHub repository's settings.
    - Access the "Secrets" section.
    - Add the following secrets for secure AWS access:
        - `AWS_ACCESS_KEY_ID`: Your AWS access key ID.
        - `AWS_SECRET_ACCESS_KEY`: Your AWS secret access key.
    Ensure these credentials have the necessary permissions to deploy the CloudFormation templates.

2. **Set Environment Variables**:
    - Confirm that the `STACK_NAME`, `S3_BUCKET_NAME`, and `AWS_DEFAULT_REGION` environment variables are appropriately set in the GitHub Actions workflow file.

3. **Triggering the Deployment**:
    - Make required changes to the CloudFormation templates or Lambda functions and commit these changes to the `main` branch.
    - This action will trigger the GitHub Actions workflow, which performs the following tasks:
        - Checks out the repository.
        - Sets up Python 3.8.
        - Installs the AWS SAM CLI.
        - Configures AWS credentials using the provided secrets.
        - Builds the SAM application in the `./cloudformation` directory.
        - Deploys the application using SAM to create or update the specified CloudFormation stack.

4. **Monitoring the Deployment**:
    - Monitor the deployment process via the Actions tab in the GitHub repository following your push to `main`.

## Solutions Description

### IAM User Activity Analysis and Removal of Unused Permissions

**Purpose:** Analyzes IAM user activity to identify permissions that are not being used.

**Features:**
- Scans IAM user activities and permissions.
- Identifies unused permissions based on user activity logs.
- Automates the removal process of unused permissions to tighten security.

**Use Case:** Best suited for maintaining a principle of least privilege and compliance with security best practices.

### Access Key Management

**Purpose:** Manages IAM user access keys by identifying and removing outdated or unused keys.

**Features:**
- Lists all IAM user access keys across the account.
- Checks for access keys that haven't been used recently.
- Deletes old access keys and issues new ones as necessary.

**Use Case:** Suitable for companies with stringent security policies that mandate frequent key rotation for enhanced protection against credential compromise.

### Access Key Rotation

**Purpose:** Automates the process of rotating IAM user access keys for enhanced security.

**Features:**
- Monitors the age of access keys and rotates them periodically.
- Creates new access keys and updates them in AWS Secrets Manager.
- Notifies via SNS about the rotation for user action.

**Use Case:** Crucial for organizations where IAM users access AWS services programmatically, maintaining key freshness and security integrity.

### Empty IAM Group Deletion

**Purpose:** Cleans up IAM by identifying and deleting IAM groups that have no members.

**Features:**
- Lists all IAM groups and checks for the presence of users.
- Removes empty groups to declutter the IAM space.
- Sends notifications upon deletion of any groups.

**Use Case:** Helps maintain an organized and efficient IAM structure, by removing unused IAM Groups.

### IAM User Console Access Management

**Purpose:** Manages console access for IAM users, ensuring secure and timely updates to access credentials.

**Features:**
- Monitors IAM users for console login patterns.
- Updates secrets in AWS Secrets Manager for access management.
- Enforces password policies and updates for secure access.

**Use Case:** Essential for organizations that need to control and audit console access within their AWS environment.

## Contributing
I welcome contributions to this repository. If you have suggestions or improvements, please submit a pull request or open an issue.
