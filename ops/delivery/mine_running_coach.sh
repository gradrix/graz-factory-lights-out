#!/bin/sh
# Mine running-coach tasks on the rig: mine_running_coach.sh HOME_LAB_GIT OUT STORE COMMITS
# The variables satisfy running-coach's test isolation guard; database/LLM/Garmin tests are deselected.
set -eu
exec python3 "$(dirname "$0")/mine.py" "$1" services/running-coach "$2" --store "$3" --commits "$4" \
  --env RUNNING_COACH_TEST_ISOLATED=1 --env POSTGRES_HOST=127.0.0.1 --env POSTGRES_PORT=5432 \
  --env POSTGRES_USER=coach_test --env POSTGRES_DB=coach_test --env POSTGRES_PASSWORD=disposable_test_only \
  --env DISCORD_BOT_TOKEN=fake-test-token --env GARMIN_TOKENSTORE=/tmp/garmin_tokens
