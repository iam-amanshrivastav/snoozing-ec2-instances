# Lambda function script for starting the EC2 instances based on their TAGs as well as it’ll check whole account
# if any server have TAGs as well as those server which TAGs mismatched or not having TAGs
# In the SNS notification we'll get all the started servers and those server not started with there reason why it's fail

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
    missing_tag_instances = []

    # Retrieve all EC2 instances in the region
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

            # Allow a 5-minute execution window
            time_format = "%H:%M"
            now_dt = datetime.datetime.strptime(now, time_format)
            start_time_dt = datetime.datetime.strptime(start_time, time_format) if start_time else None

            # Start the instance if the conditions match within the time window
            if snoozing_status == "Yes" and start_time and start_time_dt and start_time_dt <= now_dt <= (start_time_dt + datetime.timedelta(minutes=5)) and instance_state == 'stopped':
                print(f"Starting instance: {instance_name} ({instance_id})")
                try:
                    ec2.start_instances(InstanceIds=[instance_id])
                    affected_instances.append(f"Started: {instance_name} ({instance_id}, {instance_type})")
                except Exception as e:
                    print(f"Error starting instance {instance_id}: {e}")

            # Identify instances missing tags or not set for snoozing
            elif snoozing_status != "Yes" or not start_time:
                missing_tag_instances.append(f"Hi, this machine ({instance_name}, {instance_id}, {instance_type}) is either not in snoozing or tags are missing. Kindly review it.")

    # Build the SNS email report
    email_message = "AWS EC2 Instance Startup Report\n\n"
    if affected_instances:
        email_message += "Successfully Started Instances:\n" + "\n".join(affected_instances) + "\n\n"
    if missing_tag_instances:
        email_message += "Review Required for Instances:\n" + "\n".join(missing_tag_instances) + "\n\n"

    # Send SNS notification
    if affected_instances or missing_tag_instances:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=email_message,
            Subject="AWS EC2 Start Notification"
        )

    return {"status": "Start process completed", "affected_instances": affected_instances, "missing_tag_instances": missing_tag_instances}
