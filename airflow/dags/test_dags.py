from airflow import DAG,settings
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import pprint
import time
import pendulum
from airflow.operators.subdag_operator import SubDagOperator
from math import ceil

local_tz = pendulum.timezone("Asia/Seoul")
thisYear = datetime.now().year 
thisMonth = datetime.now().month -1 
thisDate = datetime.now().day
thisDate = 1 if thisDate ==31 else thisDate


default_args = {
    'owner': 'fidel',
    'start_date': datetime(thisYear, thisMonth, thisDate, tzinfo=local_tz),
    'email': ['fidel@crunchprice.com'],
    'email_on_failure': True,
    'email_on_retry': True,
    'retries': 3,
    'schedule_interval':'20 0 * * *',
    'retry_delay': timedelta(seconds=5),
    'provide_context':True,
    'depends_on_past': False,
}
dag_name='test_dags'

dag = DAG(dag_name,schedule_interval=default_args['schedule_interval'],dagrun_timeout=timedelta(hours=5),default_args=default_args,concurrency=8, catchup=False)


def run_python_tasks(words,**kwargs):
    print(words)

prepare_job = PythonOperator(
    task_id='prepare_crunchprice_data',
    python_callable=run_python_tasks,
    op_kwargs={
        'dataObject': {},
        'parentDagId':dag_name,
        'task_name':'test task 1',
        'words':'awesome',
        
    },
    dag=dag
)
