# Copyright 2017 AT&T Intellectual Property.  All other rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from datetime import timedelta

import airflow
import failure_handlers
from airflow import DAG
from airflow.operators import ConcurrencyCheckOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.subdag_operator import SubDagOperator

from deckhand_get_design import get_design_deckhand
from destroy_node import destroy_server
from drydock_deploy_site import deploy_site_drydock
from preflight_checks import all_preflight_checks
from validate_site_design import validate_site_design
"""
redeploy_server is the top-level orchestration DAG for redeploying a
server using the Undercloud platform.
"""

ALL_PREFLIGHT_CHECKS_DAG_NAME = 'preflight'
DAG_CONCURRENCY_CHECK_DAG_NAME = 'dag_concurrency_check'
DECKHAND_GET_DESIGN_VERSION = 'deckhand_get_design_version'
DESTROY_SERVER_DAG_NAME = 'destroy_server'
DRYDOCK_BUILD_DAG_NAME = 'drydock_build'
PARENT_DAG_NAME = 'redeploy_server'
VALIDATE_SITE_DESIGN_DAG_NAME = 'validate_site_design'

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': airflow.utils.dates.days_ago(1),
    'email': [''],
    'email_on_failure': False,
    'email_on_retry': False,
    'provide_context': True,
    'retries': 0,
    'retry_delay': timedelta(seconds=30),
}

dag = DAG(PARENT_DAG_NAME, default_args=default_args, schedule_interval=None)
"""
Define push function to store the content of 'action' that is
defined via 'dag_run' in XCOM so that it can be used by the
Operators
"""


def xcom_push(**kwargs):
    # Pushes action XCom
    kwargs['ti'].xcom_push(key='action',
                           value=kwargs['dag_run'].conf['action'])


action_xcom = PythonOperator(
    task_id='action_xcom', dag=dag, python_callable=xcom_push)

concurrency_check = ConcurrencyCheckOperator(
    task_id=DAG_CONCURRENCY_CHECK_DAG_NAME,
    on_failure_callback=failure_handlers.step_failure_handler,
    dag=dag)

preflight = SubDagOperator(
    subdag=all_preflight_checks(
        PARENT_DAG_NAME, ALL_PREFLIGHT_CHECKS_DAG_NAME, args=default_args),
    task_id=ALL_PREFLIGHT_CHECKS_DAG_NAME,
    on_failure_callback=failure_handlers.step_failure_handler,
    dag=dag)

get_design_version = SubDagOperator(
    subdag=get_design_deckhand(
        PARENT_DAG_NAME, DECKHAND_GET_DESIGN_VERSION, args=default_args),
    task_id=DECKHAND_GET_DESIGN_VERSION,
    on_failure_callback=failure_handlers.step_failure_handler,
    dag=dag)

validate_site_design = SubDagOperator(
    subdag=validate_site_design(
        PARENT_DAG_NAME, VALIDATE_SITE_DESIGN_DAG_NAME, args=default_args),
    task_id=VALIDATE_SITE_DESIGN_DAG_NAME,
    on_failure_callback=failure_handlers.step_failure_handler,
    dag=dag)

destroy_server = SubDagOperator(
    subdag=destroy_server(
        PARENT_DAG_NAME, DESTROY_SERVER_DAG_NAME, args=default_args),
    task_id=DESTROY_SERVER_DAG_NAME,
    on_failure_callback=failure_handlers.step_failure_handler,
    dag=dag)

drydock_build = SubDagOperator(
    subdag=deploy_site_drydock(
        PARENT_DAG_NAME, DRYDOCK_BUILD_DAG_NAME, args=default_args),
    task_id=DRYDOCK_BUILD_DAG_NAME,
    on_failure_callback=failure_handlers.step_failure_handler,
    dag=dag)

# DAG Wiring
concurrency_check.set_upstream(action_xcom)
preflight.set_upstream(concurrency_check)
get_design_version.set_upstream(preflight)
validate_site_design.set_upstream(get_design_version)
destroy_server.set_upstream(validate_site_design)
drydock_build.set_upstream(destroy_server)
