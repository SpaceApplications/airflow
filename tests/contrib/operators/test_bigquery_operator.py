# -*- coding: utf-8 -*-
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import unittest
import warnings
from datetime import datetime

import six

from airflow import configuration, models
from airflow.models import TaskInstance, DAG

from airflow.contrib.operators.bigquery_operator import \
    BigQueryCreateExternalTableOperator, BigQueryCreateEmptyTableOperator, \
    BigQueryDeleteDatasetOperator, BigQueryCreateEmptyDatasetOperator, \
    BigQueryOperator
from airflow.settings import Session

try:
    from unittest import mock
except ImportError:
    try:
        import mock
    except ImportError:
        mock = None

TASK_ID = 'test-bq-create-table-operator'
TEST_DATASET = 'test-dataset'
TEST_GCP_PROJECT_ID = 'test-project'
TEST_TABLE_ID = 'test-table-id'
TEST_GCS_BUCKET = 'test-bucket'
TEST_GCS_DATA = ['dir1/*.csv']
TEST_SOURCE_FORMAT = 'CSV'
DEFAULT_DATE = datetime(2015, 1, 1)
TEST_DAG_ID = 'test-bigquery-operators'


class BigQueryCreateEmptyTableOperatorTest(unittest.TestCase):

    @mock.patch('airflow.contrib.operators.bigquery_operator.BigQueryHook')
    def test_execute(self, mock_hook):
        operator = BigQueryCreateEmptyTableOperator(task_id=TASK_ID,
                                                    dataset_id=TEST_DATASET,
                                                    project_id=TEST_GCP_PROJECT_ID,
                                                    table_id=TEST_TABLE_ID)

        operator.execute(None)
        mock_hook.return_value \
            .get_conn() \
            .cursor() \
            .create_empty_table \
            .assert_called_once_with(
                dataset_id=TEST_DATASET,
                project_id=TEST_GCP_PROJECT_ID,
                table_id=TEST_TABLE_ID,
                schema_fields=None,
                time_partitioning={},
                labels=None
            )


class BigQueryCreateExternalTableOperatorTest(unittest.TestCase):

    @mock.patch('airflow.contrib.operators.bigquery_operator.BigQueryHook')
    def test_execute(self, mock_hook):
        operator = BigQueryCreateExternalTableOperator(
            task_id=TASK_ID,
            destination_project_dataset_table='{}.{}'.format(
                TEST_DATASET, TEST_TABLE_ID
            ),
            schema_fields=[],
            bucket=TEST_GCS_BUCKET,
            source_objects=TEST_GCS_DATA,
            source_format=TEST_SOURCE_FORMAT
        )

        operator.execute(None)
        mock_hook.return_value \
            .get_conn() \
            .cursor() \
            .create_external_table \
            .assert_called_once_with(
                external_project_dataset_table='{}.{}'.format(
                    TEST_DATASET, TEST_TABLE_ID
                ),
                schema_fields=[],
                source_uris=['gs://{}/{}'.format(TEST_GCS_BUCKET, source_object)
                             for source_object in TEST_GCS_DATA],
                source_format=TEST_SOURCE_FORMAT,
                compression='NONE',
                skip_leading_rows=0,
                field_delimiter=',',
                max_bad_records=0,
                quote_character=None,
                allow_quoted_newlines=False,
                allow_jagged_rows=False,
                src_fmt_configs={},
                labels=None
            )


class BigQueryDeleteDatasetOperatorTest(unittest.TestCase):
    @mock.patch('airflow.contrib.operators.bigquery_operator.BigQueryHook')
    def test_execute(self, mock_hook):
        operator = BigQueryDeleteDatasetOperator(
            task_id=TASK_ID,
            dataset_id=TEST_DATASET,
            project_id=TEST_GCP_PROJECT_ID
        )

        operator.execute(None)
        mock_hook.return_value \
            .get_conn() \
            .cursor() \
            .delete_dataset \
            .assert_called_once_with(
                dataset_id=TEST_DATASET,
                project_id=TEST_GCP_PROJECT_ID
            )


class BigQueryCreateEmptyDatasetOperatorTest(unittest.TestCase):
    @mock.patch('airflow.contrib.operators.bigquery_operator.BigQueryHook')
    def test_execute(self, mock_hook):
        operator = BigQueryCreateEmptyDatasetOperator(
            task_id=TASK_ID,
            dataset_id=TEST_DATASET,
            project_id=TEST_GCP_PROJECT_ID
        )

        operator.execute(None)
        mock_hook.return_value \
            .get_conn() \
            .cursor() \
            .create_empty_dataset \
            .assert_called_once_with(
                dataset_id=TEST_DATASET,
                project_id=TEST_GCP_PROJECT_ID,
                dataset_reference={}
            )


class BigQueryOperatorTest(unittest.TestCase):
    def test_bql_deprecation_warning(self):
        with warnings.catch_warnings(record=True) as w:
            BigQueryOperator(
                task_id='test_deprecation_warning_for_bql',
                bql='select * from test_table'
            )
        self.assertIn(
            'Deprecated parameter `bql`',
            w[0].message.args[0])

    def setUp(self):
        configuration.conf.load_test_config()
        self.dagbag = models.DagBag(
            dag_folder='/dev/null', include_examples=True)
        self.args = {'owner': 'airflow', 'start_date': DEFAULT_DATE}
        self.dag = DAG(TEST_DAG_ID, default_args=self.args)

    def tearDown(self):
        session = Session()
        session.query(models.TaskInstance).filter_by(
            dag_id=TEST_DAG_ID).delete()
        session.query(models.TaskFail).filter_by(
            dag_id=TEST_DAG_ID).delete()
        session.commit()
        session.close()

    @mock.patch('airflow.contrib.operators.bigquery_operator.BigQueryHook')
    def test_execute(self, mock_hook):
        operator = BigQueryOperator(
            task_id=TASK_ID,
            sql='Select * from test_table',
            destination_dataset_table=None,
            write_disposition='WRITE_EMPTY',
            allow_large_results=False,
            flatten_results=None,
            bigquery_conn_id='bigquery_default',
            udf_config=None,
            use_legacy_sql=True,
            maximum_billing_tier=None,
            maximum_bytes_billed=None,
            create_disposition='CREATE_IF_NEEDED',
            schema_update_options=(),
            query_params=None,
            labels=None,
            priority='INTERACTIVE',
            time_partitioning=None,
            api_resource_configs=None,
            cluster_fields=None,
        )

        operator.execute(None)
        mock_hook.return_value \
            .get_conn() \
            .cursor() \
            .run_query \
            .assert_called_once_with(
                sql='Select * from test_table',
                destination_dataset_table=None,
                write_disposition='WRITE_EMPTY',
                allow_large_results=False,
                flatten_results=None,
                udf_config=None,
                maximum_billing_tier=None,
                maximum_bytes_billed=None,
                create_disposition='CREATE_IF_NEEDED',
                schema_update_options=(),
                query_params=None,
                labels=None,
                priority='INTERACTIVE',
                time_partitioning=None,
                api_resource_configs=None,
                cluster_fields=None,
            )

    @mock.patch('airflow.contrib.operators.bigquery_operator.BigQueryHook')
    def test_bigquery_operator_defaults(self, mock_hook):

        operator = BigQueryOperator(
            task_id=TASK_ID,
            sql='Select * from test_table',
            dag=self.dag, default_args=self.args
        )

        operator.execute(None)
        mock_hook.return_value \
            .get_conn() \
            .cursor() \
            .run_query \
            .assert_called_once_with(
                sql='Select * from test_table',
                destination_dataset_table=None,
                write_disposition='WRITE_EMPTY',
                allow_large_results=False,
                flatten_results=None,
                udf_config=None,
                maximum_billing_tier=None,
                maximum_bytes_billed=None,
                create_disposition='CREATE_IF_NEEDED',
                schema_update_options=(),
                query_params=None,
                labels=None,
                priority='INTERACTIVE',
                time_partitioning=None,
                api_resource_configs=None,
                cluster_fields=None,
            )

        self.assertTrue(isinstance(operator.sql, six.string_types))
        ti = TaskInstance(task=operator, execution_date=DEFAULT_DATE)
        ti.render_templates()
        self.assertTrue(isinstance(ti.task.sql, six.string_types))
