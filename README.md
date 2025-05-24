# AWS EC2 Automated Snoozing & Notifications 
This project implements automated server snoozing and unsnoozing for AWS EC2 instances using Lambda functions, EventBridge scheduling, and SNS notifications. The system reads instance tags and manages scheduled shutdowns and startups while notifying the cloud team via AWS SNS.

# Features
✅ Automated daily snoozing based on EC2 tags

✅ Two Lambda functions for independent Start/Stop logic

✅ AWS SNS notifications to alert account owners

✅ EventBridge scheduling (cron-based execution at 6 AM UTC, Mon-Fri)

✅ Logs instance details (ID, Name, Type) in notifications

✅ Flexible snoozing setup via EC2 tags

# Project Architecture
EC2 Tag-Based Scheduling
Each instance should be tagged with scheduling details:
| Tag Key | Value (Example) | 
| Snoozing | Yes or No | 
| server-start-mon-friday | 06:00 (UTC) | 
| server-stop-mon-friday | 18:00 (UTC) | 


- If Snoozing=Yes, the automation applies.
- If Snoozing=No, the server remains unaffected.
- The system starts/stops instances only at the tagged time.

# Create SNS Topics for Notifications
You'll need two SNS topics for alerts:
- Server-Start-Alerts → Notifies when instances start
- Server-Stop-Alerts → Notifies when instances stop

# Steps to Set Up SNS:
Go to AWS SNS Console
Create a Standard SNS Topic (Server-Start-Alerts & Server-Stop-Alerts)
Add email subscribers (Account owner, Cloud team)
Confirm the subscription from emai

# IAM Role for Lambda
Each Lambda function needs permissions to start/stop EC2 instances and send SNS notifications

for this project you can use full access for below services. Generally we go with least previledge access.

ec2 full access
sns full access
cloudwatch full access
eventbridge full access
cloudtrail full access

# Deploy Lambda Functions
Lambda Function: Starting Instances (Start Lambda)
set the timeout value 

``` 10 ```

Lambda Function: Stopping Instances (Stop Lambda)
set the timout value

``` 10 ```


# Setup EventBridge for Scheduling
Steps to Configure EventBridge 
1. Go to AWS EventBridge Console
2. Click Rules → Create Rule
3. Rule Name: "Server-Snoozing-Hourly"
4. Choose Schedule-based trigger
5. Set the cron expression for execution at 6 AM UTC, Monday-Friday

# Cron Job in the eventbridge will be 

``` cron(0 6 ? * MON-FRI *) ```

Choose Lambda as Target:
- Attach Start Lambda to one rule
- Attach Stop Lambda to another
