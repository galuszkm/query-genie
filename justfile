# https://just.systems/man/en/

# SETTINGS

set dotenv-load := true

# Set shell based on OS
set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]
set shell := ["bash", "-cu"]

# VARIABLES

PACKAGE := "agentic-dev"
SOURCES := "backend/src mcp_postgres/src agent_service/src"
TESTS := "backend/tests mcp_postgres/tests agent_service/tests"

# DEFAULTS

# display help information
default:
    @just --list

# IMPORTS

import 'tasks/check.just'
import 'tasks/clean.just'
import 'tasks/commit.just'
import 'tasks/format.just'
import 'tasks/install.just'
import 'tasks/test.just'
