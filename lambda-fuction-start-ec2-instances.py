# Lambda function script for starting the server based on the snoozing tags

# This Lambda function will check the ec2 instance tag if in the snoozing value will have "Yes" then lambda function will be triggered and start those ec2 instance based on their timings

import boto3
import datetime
import pytz

ec2 = boto3.client('ec2')
sns = boto3.client('sns')

SNS_TOPIC_ARN = "arn:aws:sns:eu-west-1:619071349184:Server-start-alert"

def lambda_handler(event, context):
    now = datetime.datetime.now(pytz.utc).strftime("%H:%M")
    affected_instances = []

    filters = [{'Name': 'tag:Snoozing', 'Values': ['Yes']}]
    instances = ec2.describe_instances(Filters=filters)

    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            instance_type = instance['InstanceType']
            
            tags = {t['Key']: t['Value'] for t in instance.get('Tags', [])}
            instance_name = tags.get("Name", "Unnamed")
            start_time = tags.get("server-start-mon-friday", "")

            if now == start_time and instance['State']['Name'] == 'stopped':
                ec2.start_instances(InstanceIds=[instance_id])
                affected_instances.append(f"Started: {instance_name} ({instance_id}, {instance_type})")

    if affected_instances:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=f"Instances Started:\n" + "\n".join(affected_instances),
            Subject="AWS EC2 Start Notification"
        )

    return {"status": "Start process completed", "affected_instances": affected_instances}



