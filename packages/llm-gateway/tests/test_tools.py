"""Tests for LLM Gateway database tools — security-critical code.

These tools give an LLM-driven ReAct agent direct database access.
Every safety guard must be tested explicitly because a bypass means
arbitrary SQL execution against production data.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from unlock_llm_gateway.tools import describe_table, execute_sql, list_tables

# ============================================================================
# execute_sql — the security-critical function
# ============================================================================


class TestExecuteSqlRejection:
    """execute_sql must reject anything that isn't a clean SELECT."""

    def test_rejects_insert(self):
        result = json.loads(execute_sql("INSERT INTO unlock.people VALUES (1, 'test')"))
        assert "error" in result
        assert "SELECT" in result["error"]

    def test_rejects_update(self):
        result = json.loads(execute_sql("UPDATE unlock.people SET name = 'hacked'"))
        assert "error" in result

    def test_rejects_delete(self):
        result = json.loads(execute_sql("DELETE FROM unlock.people"))
        assert "error" in result

    def test_rejects_drop_table(self):
        result = json.loads(execute_sql("DROP TABLE unlock.people"))
        assert "error" in result

    def test_rejects_truncate(self):
        result = json.loads(execute_sql("TRUNCATE unlock.people"))
        assert "error" in result

    def test_rejects_embedded_semicolons(self):
        """Semicolons indicate stacked queries — must be rejected even if it starts with SELECT."""
        result = json.loads(execute_sql("SELECT 1; DROP TABLE unlock.people"))
        assert "error" in result

    def test_rejects_semicolon_between_selects(self):
        """Even two SELECTs separated by semicolons must be rejected."""
        result = json.loads(execute_sql("SELECT 1; SELECT 2"))
        assert "error" in result

    def test_allows_trailing_semicolon_on_single_select(self):
        """A single SELECT with a trailing semicolon is safe (stripped before check)."""
        # This should pass the pre-checks and reach the engine.
        # We mock the engine to avoid needing a real DB.
        with patch("unlock_llm_gateway.tools.get_sync_engine") as mock_get_engine:
            mock_conn = MagicMock()
            mock_result = MagicMock()
            mock_result.keys.return_value = ["x"]
            mock_result.fetchmany.return_value = [(1,)]
            mock_get_engine.return_value.connect.return_value.__enter__.return_value = mock_conn
            mock_conn.execute.return_value = mock_result

            result = json.loads(execute_sql("SELECT 1;"))

        assert isinstance(result, list)


class TestExecuteSqlExecution:
    """execute_sql must set safety guards when executing against the database."""

    @patch("unlock_llm_gateway.tools.get_sync_engine")
    def test_sets_read_only_transaction(self, mock_get_engine):
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.keys.return_value = ["id"]
        mock_result.fetchmany.return_value = []
        mock_get_engine.return_value.connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value = mock_result

        execute_sql("SELECT 1")

        executed_stmts = [str(call.args[0]) for call in mock_conn.execute.call_args_list]
        assert any("READ ONLY" in stmt for stmt in executed_stmts)

    @patch("unlock_llm_gateway.tools.get_sync_engine")
    def test_sets_statement_timeout(self, mock_get_engine):
        """Must set statement_timeout to prevent runaway queries from the LLM."""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.keys.return_value = ["id"]
        mock_result.fetchmany.return_value = []
        mock_get_engine.return_value.connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value = mock_result

        execute_sql("SELECT 1")

        executed_stmts = [str(call.args[0]) for call in mock_conn.execute.call_args_list]
        assert any("statement_timeout" in stmt for stmt in executed_stmts)

    @patch("unlock_llm_gateway.tools.get_sync_engine")
    def test_returns_json_rows(self, mock_get_engine):
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.keys.return_value = ["id", "name"]
        mock_result.fetchmany.return_value = [(1, "Alice"), (2, "Bob")]
        mock_get_engine.return_value.connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value = mock_result

        result = json.loads(execute_sql("SELECT id, name FROM unlock.people"))

        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Bob"

    @patch("unlock_llm_gateway.tools.get_sync_engine")
    def test_limits_to_500_rows(self, mock_get_engine):
        """fetchmany(500) must be used, not fetchall()."""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.keys.return_value = ["id"]
        mock_result.fetchmany.return_value = []
        mock_get_engine.return_value.connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value = mock_result

        execute_sql("SELECT 1")

        mock_result.fetchmany.assert_called_once_with(500)

    @patch("unlock_llm_gateway.tools.get_sync_engine")
    def test_db_exception_returns_error_json(self, mock_get_engine):
        mock_conn = MagicMock()
        mock_conn.execute.side_effect = Exception("connection refused")
        mock_get_engine.return_value.connect.return_value.__enter__.return_value = mock_conn

        result = json.loads(execute_sql("SELECT 1"))

        assert "error" in result
        assert "connection refused" in result["error"]


# ============================================================================
# list_tables
# ============================================================================


class TestListTables:
    @patch("unlock_llm_gateway.tools.get_sync_engine")
    def test_returns_table_list(self, mock_get_engine):
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.keys.return_value = ["schemaname", "tablename", "approximate_row_count"]
        mock_result.fetchall.return_value = [
            ("unlock", "people", 100),
            ("unlock", "orgs", 50),
        ]
        mock_get_engine.return_value.connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value = mock_result

        result = json.loads(list_tables())

        assert len(result) == 2
        assert result[0]["tablename"] == "people"

    @patch("unlock_llm_gateway.tools.get_sync_engine")
    def test_db_error_returns_error_json(self, mock_get_engine):
        mock_conn = MagicMock()
        mock_conn.execute.side_effect = Exception("timeout")
        mock_get_engine.return_value.connect.return_value.__enter__.return_value = mock_conn

        result = json.loads(list_tables())

        assert "error" in result


# ============================================================================
# describe_table
# ============================================================================


class TestDescribeTable:
    @patch("unlock_llm_gateway.tools.get_sync_engine")
    def test_returns_column_metadata(self, mock_get_engine):
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.keys.return_value = [
            "column_name", "data_type", "is_nullable",
            "column_default", "character_maximum_length",
        ]
        mock_result.fetchall.return_value = [
            ("id", "uuid", "NO", "gen_random_uuid()", None),
            ("name", "text", "YES", None, None),
        ]
        mock_get_engine.return_value.connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value = mock_result

        result = json.loads(describe_table("people"))

        assert len(result) == 2
        assert result[0]["column_name"] == "id"

    @patch("unlock_llm_gateway.tools.get_sync_engine")
    def test_uses_parameterized_query(self, mock_get_engine):
        """Table name must be passed as a parameter, not interpolated into SQL."""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.keys.return_value = []
        mock_result.fetchall.return_value = []
        mock_get_engine.return_value.connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value = mock_result

        # Pass a malicious table name — it must go through parameterized query
        describe_table("people; DROP TABLE unlock.people")

        call_args = mock_conn.execute.call_args
        # Second positional arg should be the parameter dict
        assert call_args[0][1] == {"table_name": "people; DROP TABLE unlock.people"}
