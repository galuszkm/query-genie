# run check tasks
[group("check")]
check: format check-hooks check-code check-type check-security check-audit

# check code quality
[group("check")]
check-code:
    uv run ruff check {{SOURCES}} {{TESTS}}

# check code format
[group("check")]
check-format:
    uv run ruff format --check {{SOURCES}} {{TESTS}}

# check code security
[group("check")]
check-security:
    uv run bandit --recursive --configfile=pyproject.toml {{SOURCES}}

# check code typing
[group("check")]
check-type:
    uv run mypy --explicit-package-bases {{SOURCES}} {{TESTS}}

# check code typing with strict settings (ignores disable_error_code from pyproject.toml)
[group("check")]
check-type-strict:
    uv run mypy \
        --enable-error-code=assignment \
        --enable-error-code=no-redef \
        --enable-error-code=union-attr \
        --enable-error-code=attr-defined \
        --enable-error-code=no-any-return \
        {{SOURCES}} {{TESTS}}

# check pre-commit hooks
[group("check")]
check-hooks:
    uv run pre-commit run --all-files

# scan for vulnerabilities in dependencies
[group("check")]
check-audit:
    uv export --no-hashes --format requirements-txt > .req.txt
    uv run pip-audit --requirement .req.txt
    rm .req.txt
