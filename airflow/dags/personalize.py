from airflow import DAG, settings
from airflow.models import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import pprint
import time
import pendulum
import pandas as pd
import random
import numpy as np
import os
import logging
import json
import boto3

from pandas import DataFrame
from pymongo import MongoClient
from airflow.operators.subdag_operator import SubDagOperator
from math import ceil

from airflow.plugins_manager import AirflowPlugin
from airflow.utils.decorators import apply_defaults
from airflow.operators.sensors import BaseSensorOperator


local_tz = pendulum.timezone("Asia/Seoul")
thisYear = datetime.now().year
thisMonth = datetime.now().month - 1
thisDate = datetime.now().day
thisDate = 1 if thisDate == 31 else thisDate


default_args = {
    'owner': 'fidel',
    'start_date': datetime(thisYear, thisMonth, thisDate, tzinfo=local_tz),
    'retries': 3,
    'retry_delay': timedelta(minutes=3),
    'schedule_interval': '20 0 * * *',
    'provide_context': True,
    'depends_on_past': False,
}
dag_name = 'personalize_test'

dag = DAG(dag_name, schedule_interval=default_args['schedule_interval'], dagrun_timeout=timedelta(
    hours=5), default_args=default_args, concurrency=8, catchup=False)

bucket = 'personalize-s3-data'
filename = 'crunchprice.csv'
# solutionVersionArn = ''


#Xcom
#make csv file
def make_csv(**kwargs):
    db = []

    # url = os.environ.get("MONGO_URI")
    client = MongoClient('mongodb://admin:Crunch5757@13.125.209.221:27017')
    table = client['crunchprice'].personalize_table.find({}, {'_id': False, 'ORIGINAL_USER_ID': False})
    for info in table:
        db.append(info)

    data = pd.DataFrame(db)
    data.to_csv(filename)
    s3 = boto3.client('s3', region_name='us-east-1', aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'), aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'))
    boto3.Session().resource('s3').Bucket(bucket).Object(filename).upload_file(filename)



#update csv file
update_csv = PythonOperator(
    task_id='update_personalize_csv',
    python_callable=make_csv,
    provide_context=True,
    dag=dag
)

#  update dataset import job
def make_dataset_import_job(**kwargs):
    suffix = str(np.random.uniform())[4:9]
    personalize = boto3.client('personalize', region_name='us-east-1', aws_access_key_id=os.environ.get(
        'AWS_ACCESS_KEY_ID'), aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'))
    response = personalize.create_dataset_import_job(
        jobName='crunch-dataset-import-job' + suffix,
        # datasetArn 은 변화 없을 값
        datasetArn='arn:aws:personalize:us-east-1:051972272913:dataset/crunch-personalize-dataset-groupV2/INTERACTIONS',
        dataSource={'dataLocation': 's3://personalize-s3-data/crunchprice.csv'},
        roleArn=os.environ.get('ROLE_ARN'))

    dsij_arn = response['datasetImportJobArn']
    description = personalize.describe_dataset_import_job(
        datasetImportJobArn=dsij_arn)['datasetImportJob']

    logging.info('##########')
    logging.info(suffix)
    logging.info(description)
    logging.info(description['status'])
    logging.info('##########')

    # if description['status'] != 'ACTIVE':
    #     logging.info('response not active')
    #     raise ValueError('response pending')

    # i = 0
    while description['status'] != 'ACTIVE':
        time.sleep(60)
        description = personalize.describe_dataset_import_job(
        datasetImportJobArn=dsij_arn)['datasetImportJob']
        logging.info('Progress: ' + str(description['status']))
    # print('Status: ' + description['status'])
    # if description['status'] == 'ACTIVE':
    # or 'CREATE PENDING' will be returned


update_dataset_import_job = PythonOperator(
            task_id = 'update_dataset_import_job',
            python_callable = make_dataset_import_job,
            provide_context = True,
            execution_timeout=timedelta(minutes=60),
            dag = dag
        )


# 특정 레시피를 선택해서 Create Solution 하는 함수
# def create_solution(**kwargs):
#     recipe_arn = "arn:aws:personalize:::recipe/aws-hrnn"
#     create_solution_response = personalize.create_solution(
#         name = "DEMO-temporal-solution-"+suffix,
#         datasetGroupArn = dataset_group_arn,
#         recipeArn = recipe_arn,
#     )

# update solution version
def make_new_solution_version(**kwargs):
    personalize = boto3.client('personalize', region_name='us-east-1', aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'), aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'))
    response = personalize.create_solution_version(
        solutionArn = 'arn:aws:personalize:us-east-1:051972272913:solution/crunch-solutionV3'
    )
    logging.info('Response: ' + str(response))

    description = personalize.describe_solution_version(
        solutionVersionArn = response['solutionVersionArn']
    )

    status = description["solutionVersion"]["status"]
    # logging.info('Progress: ' + str(description['solutionVersion']['status']))
    # logging.info('Response@@@@@: ' + str(response))
    # logging.info('Response@@@@@: ' + str(response['solutionVersionArn']))
    # logging.info('Response@@@@@: ' + json.dumps(response['solutionVersionArn']))

    while description["solutionVersion"]["status"] != 'ACTIVE':
        time.sleep(30)
        description = personalize.describe_solution_version(
            solutionVersionArn = response['solutionVersionArn']
        )
        # logging.info('Response@@@@@: ' + str(response))
        logging.info('Progress: ' + str(description['solutionVersion']['status']))
    
    # global solutionVersionArn
    kwargs['ti'].xcom_push(key='solutionVersionArn', value=response['solutionVersionArn'])
    # solutionVersionArn = response['solutionVersionArn']
    # logging.info('solutionVersionArn: ' + str(solutionVersionArn))

update_new_solution_version = PythonOperator(
            task_id='update_new_solution_version',
            python_callable=make_new_solution_version,
            provide_context=True,
            execution_timeout=timedelta(minutes=240),
            dag=dag
)

# solution_version_arn = make_new_solution_version의 response['solutionVersionArn']
# print(solution_arn) 



#! update campaign version
def make_update_campaign_version(**kwargs):
    client= boto3.client('personalize', region_name='us-east-1', aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'), aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'))

    ti = kwargs['ti']
    pull_solutionVersionArn = ti.xcom_pull(key='solutionVersionArn', task_ids='update_new_solution_version')
    # logging.info('solutionVersionArn: ' + str(pull_solutionVersionArn))
    response = client.update_campaign(
        campaignArn='arn:aws:personalize:us-east-1:051972272913:campaign/crunch-campaignv2',
        # solutionVersionArn = 위 update solution의 response로 받아야한다
        solutionVersionArn=pull_solutionVersionArn, 
        # 응답 량 ? 업데이트 속도 ? , 비용과 관련 있는 값이라고 했습니다.
        minProvisionedTPS=100
    )

update_campagin_version = PythonOperator(
            task_id='update_campaign_version',
            python_callable=make_update_campaign_version,
            provide_context=True,
            execution_timeout=timedelta(minutes=180),
            dag=dag
)

update_csv >> update_dataset_import_job >> update_new_solution_version >> update_campagin_version

# update_new_solution_version >> update_campagin_version
