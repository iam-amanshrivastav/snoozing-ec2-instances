# Lambda function script for stopped the EC2 instances based on their TAGs as well as it’ll check whole account
# if any server have TAGs as well as those server which TAGs mismatched or not having TAGs
# In the SNS notification we'll get all the stopped servers and those server not due to any error with there reason why it's fail


import boto3
import datetime
import pytz

# AWS Clients
ec2 = boto3.client('ec2')
sns = boto3.client('sns')

SNS_TOPIC_ARN = "arn:aws:sns:eu-west-1:619071349184:Server-start-alert"

def lambda_handler(event, context):
    # Get current UTC time
    now = datetime.datetime.now(pytz.utc).strftime("%H:%M")
    print(f"Current UTC time: {now}")

    affected_instances = []
    skipped_instances = []

    # Retrieve all EC2 instances in the account
    instances = ec2.describe_instances()

    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            instance_type = instance['InstanceType']
            instance_state = instance['State']['Name']

            # Extract instance tags
            tags = {t['Key']: t['Value'] for t in instance.get('Tags', [])}
            instance_name = tags.get("Name", "Unnamed")
            start_time = tags.get("server-start-mon-friday", "").strip()
            snoozing_status = tags.get("Snoozing", "").strip()

            print(f"Checking instance: {instance_name} ({instance_id}) - State: {instance_state}, Scheduled Start Time: {start_time}, Snoozing Tag: {snoozing_status}")

            # Start instance only if 'Snoozing' is set to 'Yes' and the start time matches
            if snoozing_status == "Yes" and now == start_time and instance_state == 'stopped':
                print(f"Starting instance: {instance_name} ({instance_id})")
                try:
                    ec2.start_instances(InstanceIds=[instance_id])
                    affected_instances.append(f"Started: {instance_name} ({instance_id}, {instance_type})")
                except Exception as e:
                    print(f"Error starting instance {instance_id}: {e}")
                    skipped_instances.append(f"Failed to start: {instance_name} ({instance_id}) - Error: {e}")

            # Log instances that are missing tags or have incorrect configurations
            elif snoozing_status != "Yes" or not start_time:
                skipped_instances.append(f"Skipped: {instance_name} ({instance_id}) - Snoozing tag missing or incorrect")

    # Build the SNS email report
    email_message = "AWS EC2 Instance Startup Report\n\n"
    if affected_instances:
        email_message += " Instances Started:\n" + "\n".join(affected_instances) + "\n\n"
    if skipped_instances:
        email_message += " Instances Skipped:\n" + "\n".join(skipped_instances) + "\n\n"

    # Send SNS notification
    if affected_instances or skipped_instances:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=email_message,
            Subject="AWS EC2 Start Notification"
        )

    return {"status": "Start process completed", "affected_instances": affected_instances, "skipped_instances": skipped_instances}


