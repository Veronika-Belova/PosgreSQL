from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import pandas as pd
import os
from io import StringIO

default_args = {
    'owner': 'Veronika',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
}

def fetch_new_clients():
    command = 'curl https://9c579ca6-fee2-41d7-9396-601da1103a3b.selstorage.ru/new_clients.csv'
    output = os.popen(command).read()

    if not output:
        raise Exception("No data retrieved from the source")
    data = StringIO(output)
    df = pd.read_csv(data)
    
    if df.empty:
        raise Exception("No data in DataFrame. Please check the source CSV file.")
    
    return df

def insert_into_database(**kwargs):
    df = kwargs['ti'].xcom_pull(task_ids='fetch_new_clients_task')
    
    if df is None or df.empty:
        raise Exception("DataFrame is empty or None.")

    pg_hook = PostgresHook(postgres_conn_id='psql')
    connection = pg_hook.get_conn()
    cursor = connection.cursor()

    records = df.to_records(index=False)
    record_list = list(records)

    insert_query = """
    INSERT INTO credit_clients (Date, CustomerId, Surname, CreditScore, Geography, Gender, Age, Tenure, Balance, NumOfProducts, HasCrCard, IsActiveMember, EstimatedSalary, Exited) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    for record in record_list:
        cursor.execute(insert_query, record)
    connection.commit()
    cursor.close()
    connection.close()

with DAG('daily_clients_data_update', default_args=default_args, schedule_interval='@daily', catchup=False) as dag:
    fetch_new_clients_task = PythonOperator(
        task_id='fetch_new_clients',
        python_callable=fetch_new_clients,
        dag=dag,
    )

    insert_into_database_task = PythonOperator(
        task_id='insert_into_database',
        python_callable=insert_into_database,
        provide_context=True,
        dag=dag,
    )

fetch_new_clients_task >> insert_into_database_task 
