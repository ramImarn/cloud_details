import boto3
import sys
from datetime import datetime, timedelta
import datetime
import pandas as pd
import numpy as np
import openai
from openai import OpenAI

client = OpenAI() 

ec2_type,ec2_info,ec2_id,edc2_cpu,net_in,net_out,data_in,data_out,addres,loadb=[],[],[],[],[],[],[],[],[],[]
# Initialize Boto3 session with explicit access and secret keys
session = boto3.Session(
    region_name='us-east-1'
)

# Initialize CloudWatch client
cloudwatch_client = session.client('cloudwatch')

# Initialize EC2 client with the same region
ec2_client = session.client('ec2')

# Get list of all EC2 instances
instances = ec2_client.describe_instances()

# Get elastic ip of ec2 id
addr = ec2_client.describe_addresses()

# Get current timestamp for time range
end_time = datetime.datetime.utcnow()
start_time = end_time - datetime.timedelta(hours=1)  # Adjust time range as needed

# Metrics to fetch
metrics = ['CPUUtilization', 'NetworkIn', 'NetworkOut', 'NetworkPacketsIn', 'NetworkPacketsOut']

ec2 = session.resource('ec2')
instances_1 = ec2.instances.filter(
    Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
for instance in instances_1:
    ec2_id.append(instance.id)
    ec2_type.append(instance.instance_type)
    #print(instance.id, instance.instance_type)


for address in addr['Addresses']:
   addres.append(address['InstanceId'])

for reservation in instances['Reservations']:
    for instance in reservation['Instances']:
        instance_id = instance['InstanceId']
        instance_type = instance['InstanceType']
        #print(f"Instance ID: {instance_id}")
        print("EXTRACTING INFO ABOUT EC2 WAIT FOR WHILE!!!")
        # Retrieve metrics for this instance
        #ec2_info=[]
        for metric_name in metrics:
            # Get metric statistics
            response = cloudwatch_client.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName=metric_name,
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,  # 5-minute interval
                Statistics=['Average']
            )
            
            # Parse metric data
            if 'Datapoints' in response:
                datapoints = response['Datapoints']
                if len(datapoints) > 0:
                    average_value = datapoints[-1]['Average']  # Most recent value
                    #print(average_value)
                    #id_ins=instance_id
                    #ty_ins=instance_type
                    ec2_info.append(average_value)
                    #print(f"{metric_name}: {average_value}")
                    #ec2_info.append(f"{'instance_id'}:{instance_id},{metric_name}: {average_value}")
        #         else:
        #             print(f"No data available for {metric_name}")
        
            #print(average_value)
            #ec2_info_list.append(ec2_info)

        #     else:
        #         print(f"No data available for {metric_name}")
        
        #print(average_value)
        #ec2_id.append(instance_id)
        #ec2_type.append(instance_type)
        # print("\n")

#print(ec2_info)
if len(ec2_info) > 5:
    split_lists = [ec2_info[i:i+5] for i in range(0, len(ec2_info), 5)]   
else:
    print('no enstance isnt running!!!')

#print(split_lists)
#print(ec2_id)

fd=pd.DataFrame(split_lists,columns=metrics)
fd.insert(loc=0, column='ec2_type', value=ec2_type)
fd.insert(loc=0, column='ec2_id', value=ec2_id)

condition = [fd['CPUUtilization'] > 7,fd['CPUUtilization'] < 3, (fd['CPUUtilization'] < 7) & (fd['CPUUtilization'] > 3)]
values = ["ec2 needed to enhace","need to downgrade ec2","ec2 is healthy"]

fd['ec2_status']=np.select(condition,values)

fd['elastic_ip']=[ad in addres for ad in ec2_id]
fd['load balancer']=[ad in loadb for ad in ec2_id]

def get_completion(prompt, model="gpt-3.5-turbo"):

   messages = [{"role": "user", "content": prompt}]

   response = client.chat.completions.create(model=model,messages=messages,temperature=0)

   return response.choices[0].message.content


reply=[]
for a in fd['ec2_status']:
    if a == values[1]:
        prompt = "give next lower price ec2 instance type than t2.medium "
        reply.append(get_completion(prompt))
        #print(prompt)
    elif a == values[0]:
        prompt = "give next large ec2 instance type than t2.medium "
        reply.append(get_completion(prompt))
        #print(prompt)
    else:
        prompt = "ec2 is healty "
        reply.append(prompt)


fd.insert(loc=len(fd.columns), column='recomentation', value=reply)
fd.to_csv('aws_ec2_report_2.csv')
#print(fd)