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

from click.testing import CliRunner
from mock import patch, ANY

from shipyard_client.cli.describe.actions import DescribeAction
from shipyard_client.cli.describe.actions import DescribeStep
from shipyard_client.cli.describe.actions import DescribeValidation
from shipyard_client.cli.commands import shipyard

auth_vars = ('--os_project_domain_name=OS_PROJECT_DOMAIN_NAME_test '
             '--os_user_domain_name=OS_USER_DOMAIN_NAME_test '
             '--os_project_name=OS_PROJECT_NAME_test '
             '--os_username=OS_USERNAME_test --os_password=OS_PASSWORD_test '
             '--os_auth_url=OS_AUTH_URL_test')


def test_describe_action():
    """test describe_action"""

    action_id = '01BTG32JW87G0YKA1K29TKNAFX'
    runner = CliRunner()
    with patch.object(DescribeAction, '__init__') as mock_method:
        runner.invoke(shipyard, [auth_vars, 'describe', 'action', action_id])
    mock_method.assert_called_once_with(ANY, action_id)


def test_describe_action_negative():
    """
    negative unit test for describe action command
    verifies invalid action id results in error
    """

    action_id = 'invalid action id'
    runner = CliRunner()
    results = runner.invoke(shipyard,
                            [auth_vars, 'describe', 'action', action_id])
    assert 'Error' in results.output


def test_describe_step():
    """test describe_step"""

    step_id = 'preflight'
    action_id = '01BTG32JW87G0YKA1K29TKNAFX'
    runner = CliRunner()
    with patch.object(DescribeStep, '__init__') as mock_method:
        results = runner.invoke(shipyard, [
            auth_vars, 'describe', 'step', step_id, '--action=' + action_id
        ])
    mock_method.assert_called_once_with(ANY, action_id, step_id)


def test_describe_step_negative():
    """
    negative unit test for describe step command
    verifies invalid action id results in error
    """

    step_id = 'preflight'
    action_id = 'invalid action id'
    runner = CliRunner()
    results = runner.invoke(shipyard, [
        auth_vars, 'describe', 'step', step_id, '--action=' + action_id
    ])
    assert 'Error' in results.output


def test_describe_validation():
    """test describe_validation"""

    validation_id = '01BTG3PKBS15KCKFZ56XXXBGF2'
    action_id = '01BTG32JW87G0YKA1K29TKNAFX'
    runner = CliRunner()
    with patch.object(DescribeValidation, '__init__') as mock_method:
        runner.invoke(shipyard, [
            auth_vars, 'describe', 'validation', '01BTG3PKBS15KCKFZ56XXXBGF2',
            '--action=' + action_id
        ])
    mock_method.assert_called_once_with(ANY, validation_id, action_id)


def test_describe_validation_negative():
    """
    negative unit test for describe validation command
    verifies invalid validation id and action id results in error
    """

    validation_id = 'invalid validation id'
    action_id = '01BTG32JW87G0YKA1K29TKNAFX'
    runner = CliRunner()
    results = runner.invoke(shipyard, [
        auth_vars, 'describe', 'validation', validation_id,
        '--action=' + action_id
    ])
    assert 'Error' in results.output

    validation_id = '01BTG3PKBS15KCKFZ56XXXBGF2'
    action_id = 'invalid action id'
    runner = CliRunner()
    results = runner.invoke(shipyard, [
        auth_vars, 'describe', 'validation', validation_id,
        '--action=' + action_id
    ])
    assert 'Error' in results.output
