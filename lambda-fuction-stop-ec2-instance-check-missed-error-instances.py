# Lambda function script for stopped the EC2 instances based on their TAGs as well as it’ll check whole account
# if any server have TAGs as well as those server which TAGs mismatched or not having TAGs
# In the SNS notification we'll get all the stopped servers and those server not due to any error with there reason why it's fail


import boto3
import datetime
import pytz

# AWS Clients
ec2 = boto3.client('ec2')
sns = boto3.client('sns')

SNS_TOPIC_ARN = "arn:aws:sns:eu-west-1:619071349184:Server-stop-alerts"

def lambda_handler(event, context):
    now = datetime.datetime.now(pytz.utc).strftime("%H:%M")
    print(f"Current UTC time: {now}")

    affected_instances = []
    missing_tag_instances = []

    # Retrieve all EC2 instances
    instances = ec2.describe_instances()

    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            instance_type = instance['InstanceType']
            instance_state = instance['State']['Name']

            # Extract tags
            tags = {t['Key']: t['Value'] for t in instance.get('Tags', [])}
            instance_name = tags.get("Name", "Unnamed")
            stop_time = tags.get("server-stop-mon-friday", "").strip()
            snoozing_status = tags.get("Snoozing", "").strip()

            print(f"Checking instance: {instance_name} ({instance_id}) - State: {instance_state}, Stop Time: {stop_time}, Snoozing Tag: {snoozing_status}")

            # Execution time check (5-minute window)
            time_format = "%H:%M"
            now_dt = datetime.datetime.strptime(now, time_format)
            stop_time_dt = datetime.datetime.strptime(stop_time, time_format) if stop_time else None

            if snoozing_status == "Yes" and stop_time and stop_time_dt and stop_time_dt <= now_dt <= (stop_time_dt + datetime.timedelta(minutes=5)) and instance_state == 'running':
                print(f"Stopping instance: {instance_name} ({instance_id})")
                try:
                    ec2.stop_instances(InstanceIds=[instance_id])
                    affected_instances.append(f"Stopped: {instance_name} ({instance_id}, {instance_type})")
                except Exception as e:
                    print(f"Error stopping instance {instance_id}: {e}")

            elif snoozing_status != "Yes" or not stop_time:
                missing_tag_instances.append(f"Hi, this machine ({instance_name}, {instance_id}, {instance_type}) is either not in snoozing or tags are missing. Kindly review it.")

    email_message = "AWS EC2 Instance Shutdown Report\n\n"
    if affected_instances:
        email_message += "✅ Successfully Stopped Instances:\n" + "\n".join(affected_instances) + "\n\n"
    if missing_tag_instances:
        email_message += "⚠️ Review Required for Instances:\n" + "\n".join(missing_tag_instances) + "\n\n"

    if affected_instances or missing_tag_instances:
        sns.publish(TopicArn=SNS_TOPIC_ARN, Message=email_message, Subject="AWS EC2 Stop Notification")

    return {"status": "Stop process completed", "affected_instances": affected_instances, "missing_tag_instances": missing_tag_instances}


