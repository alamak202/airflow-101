# Import necessary modules from the Airflow package
from __future__ import annotations

import pendulum

from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

# --- 1. DEFINE A PYTHON FUNCTION ---
# This function will be called by the PythonOperator.
def print_a_message(dag_run):
    """
    This function prints the execution date and a custom message.
    Airflow passes in the 'dag_run' object that contains context about this specific run.
    """
    execution_date = dag_run.execution_date
    print(f"Hello from the PythonOperator! 👋")
    print(f"This DAG run is for the date: {execution_date.date()}")
    return "Message printed successfully!"


# --- 2. DEFINE THE DAG ---
# A DAG is a collection of all the tasks you want to run, organized in a way that reflects their relationships.
with DAG(
    # A unique identifier for your DAG.
    dag_id="my_first_github_dag",
    # Default arguments applied to all tasks in the DAG.
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        "email_on_failure": False,
        "retries": 1,
    },
    # A description of your DAG.
    description="A simple sample DAG loaded from GitHub.",
    # When the DAG should run. 'None' means it will only run when triggered manually.
    # You could change this to '@daily', '@hourly', etc.
    schedule=None,
    # The date on which the DAG should start running.
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    # If True, Airflow would schedule all missed runs since the start_date.
    # False is safer for development.
    catchup=False,
    # Tags to help filter and organize your DAGs in the UI.
    tags=["example", "github"],
) as dag:
    # Add markdown documentation that will be visible in the 'Details' tab of the DAG in the Airflow UI.
    dag.doc_md = """
    ### My First GitHub DAG

    This is a sample DAG to demonstrate loading DAGs from a GitHub repository using `git-sync`.
    - It uses the `BashOperator` to run simple shell commands.
    - It uses the `PythonOperator` to execute a Python function.
    - It shows a simple parallel dependency.
    """

    # --- 3. DEFINE TASKS ---
    # Tasks are the individual units of work in a DAG.

    # Task 1: A BashOperator that prints a starting message.
    task_start = BashOperator(
        task_id="start_task",
        bash_command='echo "Starting the sample DAG... Let\'s go!"',
    )

    # Task 2: A BashOperator that uses Jinja templating to print the execution date.
    # '{{ ds }}' is an Airflow macro that resolves to the execution date as YYYY-MM-DD.
    task_show_date = BashOperator(
        task_id="show_execution_date",
        bash_command="echo 'This DAG is running for the date: {{ ds }}'",
    )

    # Task 3: A PythonOperator that calls our defined Python function.
    task_python_message = PythonOperator(
        task_id="python_message_task",
        python_callable=print_a_message,
    )

    # Task 4: A final BashOperator to signify the end.
    task_end = BashOperator(
        task_id="end_task",
        bash_command="echo 'DAG finished successfully. Great job!'",
    )

    # --- 4. SET TASK DEPENDENCIES ---
    # This defines the order in which the tasks will be executed.
    # The 'start_task' will run first.
    # After it finishes, 'show_execution_date' and 'python_message_task' will run in parallel.
    # Once BOTH of those are complete, the 'end_task' will run.
    task_start >> [task_show_date, task_python_message] >> task_end