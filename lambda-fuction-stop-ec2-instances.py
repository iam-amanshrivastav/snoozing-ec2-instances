# Lambda function for stop the servers based on snoozing tags

# This Lambda function will check the ec2 instance tag if in the snoozing value will have "Yes" then it'll trigger the stop those ec2 instance based on their timings

import boto3
import datetime
import pytz

ec2 = boto3.client('ec2')
sns = boto3.client('sns')

SNS_TOPIC_ARN = "arn:aws:sns:eu-west-1:619071349184:Server-stop-alerts"

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
            stop_time = tags.get("server-stop-mon-friday", "")

            if now == stop_time and instance['State']['Name'] == 'running':
                ec2.stop_instances(InstanceIds=[instance_id])
                affected_instances.append(f"Stopped: {instance_name} ({instance_id}, {instance_type})")

    if affected_instances:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=f"Instances Stopped:\n" + "\n".join(affected_instances),
            Subject="AWS EC2 Stop Notification"
        )

    return {"status": "Stop process completed", "affected_instances": affected_instances}

