import json
from datetime import datetime, timedelta
import hashlib

from airflow.decorators import dag, task
from airflow.providers.http.operators.http import HttpOperator
from airflow.providers.amazon.aws.operators.s3 import S3CreateObjectOperator

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=2),
}

@dag(
    dag_id='user_data_etl_pipeline_with_api_key',
    default_args=default_args,
    description='ETL pipeline using a real API with an API key.',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['etl', 'user_data', 'api_key'],
)
def user_data_etl():
    """
    ### User Data ETL with API Key
    This pipeline fetches user data from the Reqres REST API using an API key,
    anonymizes the email, and loads the result into an S3 bucket.
    """

    # Task to fetch user data from the API
    fetch_user_data = HttpOperator(
        task_id='fetch_user_data',
        http_conn_id='user_api',          # Connection to https://reqres.in
        endpoint='api/users',
        method='GET',
        # NEW: Add the API key to the request headers
        headers={'x-api-key': 'reqres-free-v1'},
        response_filter=lambda response: response.json()['data'],
        log_response=True,
    )

    @task
    def transform_data(user_data: list) -> str:
        """
        Anonymizes email in the user data.
        """
        anonymized_users = []
        for user in user_data:
            user['email'] = hashlib.sha256(user['email'].encode()).hexdigest()
            anonymized_users.append(user)
        return json.dumps(anonymized_users, indent=4)

    anonymize_user_data = transform_data(user_data=fetch_user_data.output)

    upload_to_s3 = S3CreateObjectOperator(
        task_id='upload_to_s3',
        aws_conn_id='aws_default',
        s3_bucket='airflow-etl-data-landing-zone-2025',  # **Replace with your S3 bucket name**
        s3_key="user_data/{{ ds }}/anonymized_users.json",
        data=anonymize_user_data,
        replace=True,
    )

    # Define the task dependencies
    fetch_user_data >> anonymize_user_data >> upload_to_s3

# Instantiate the DAG
user_data_etl_dag = user_data_etl()