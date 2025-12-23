# run test tasks
[group("test")]
test: test-coverage-mcp test-coverage-backend test-coverage-service

# run all tests for all modules (separate runs to avoid sys.path conflicts)
[group("test")]
test-all:
    uv run pytest backend/tests -v --no-cov
    uv run pytest agent_service/tests -v --no-cov
    uv run pytest mcp_postgres/tests -v --no-cov

# check code coverage for mcp_postgres module
[group("test")]
test-coverage-mcp numprocesses="2" cov_fail_under="75":
    uv run python -c "from pathlib import Path; import shutil; Path('.coverage').unlink(missing_ok=True); shutil.rmtree('htmlcov', ignore_errors=True)"
    uv run pytest --numprocesses={{numprocesses}} --cov=mcp_postgres/src --cov-report=html:htmlcov/mcp_postgres --cov-report=term-missing --cov-fail-under={{cov_fail_under}} mcp_postgres/tests

# check code coverage for backend module
[group("test")]
test-coverage-backend numprocesses="2" cov_fail_under="75":
    uv run python -c "from pathlib import Path; import shutil; Path('.coverage').unlink(missing_ok=True); shutil.rmtree('htmlcov', ignore_errors=True)"
    uv run pytest --numprocesses={{numprocesses}} --cov=backend/src --cov-report=html:htmlcov/backend --cov-report=term-missing --cov-fail-under={{cov_fail_under}} backend/tests

# check code coverage for agent_service module
[group("test")]
test-coverage-service numprocesses="2" cov_fail_under="50":
    uv run python -c "from pathlib import Path; import shutil; Path('.coverage').unlink(missing_ok=True); shutil.rmtree('htmlcov', ignore_errors=True)"
    uv run pytest --numprocesses={{numprocesses}} --cov=agent_service/src --cov-report=html:htmlcov/agent_service --cov-report=term-missing --cov-fail-under={{cov_fail_under}} agent_service/tests
