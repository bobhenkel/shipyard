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

from armada_deploy_site import deploy_site_armada
from deckhand_get_design import get_design_deckhand
from drydock_deploy_site import deploy_site_drydock
from validate_site_design import validate_site_design
"""
update_site is the top-level orchestration DAG for updating a site using the
Undercloud platform.

TODO: We will disable pre-flight checks for now and will revisit it at
      a later date. The pre-flight checks will be more targeted in the
      case of 'update_site' and will include specific checks on things
      like coredns, calico and ceph.
"""

ARMADA_BUILD_DAG_NAME = 'armada_build'
DAG_CONCURRENCY_CHECK_DAG_NAME = 'dag_concurrency_check'
DECKHAND_GET_DESIGN_VERSION = 'deckhand_get_design_version'
DRYDOCK_BUILD_DAG_NAME = 'drydock_build'
PARENT_DAG_NAME = 'update_site'
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

drydock_build = SubDagOperator(
    subdag=deploy_site_drydock(
        PARENT_DAG_NAME, DRYDOCK_BUILD_DAG_NAME, args=default_args),
    task_id=DRYDOCK_BUILD_DAG_NAME,
    on_failure_callback=failure_handlers.step_failure_handler,
    dag=dag)

armada_build = SubDagOperator(
    subdag=deploy_site_armada(
        PARENT_DAG_NAME, ARMADA_BUILD_DAG_NAME, args=default_args),
    task_id=ARMADA_BUILD_DAG_NAME,
    on_failure_callback=failure_handlers.step_failure_handler,
    dag=dag)

# DAG Wiring
concurrency_check.set_upstream(action_xcom)
get_design_version.set_upstream(concurrency_check)
validate_site_design.set_upstream(get_design_version)
drydock_build.set_upstream(validate_site_design)
armada_build.set_upstream(drydock_build)
