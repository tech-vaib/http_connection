Steps:

    Create .git/hooks/commit-msg file in your local repo:

#!/bin/sh

# Regex pattern to match Jira ticket ID (customize the pattern as needed)
JIRA_PATTERN='(PROJ|TICKET|JIRA)-[0-9]+'

commit_msg=$(cat "$1")

if ! echo "$commit_msg" | grep -qE "$JIRA_PATTERN"; then
    echo "❌ Commit message must contain a Jira ticket ID (e.g., PROJ-123)"
    exit 1
fi

    Make it executable:

chmod +x .git/hooks/commit-msg



----
.github/workflows/validate-commit.yml
name: Validate Jira Ticket in Commit Message

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  check-commits:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout Code
      uses: actions/checkout@v3

    - name: Validate Commit Messages
      run: |
        echo "Checking commit messages for Jira ticket..."
        regex='(PROJ|TICKET|JIRA)-[0-9]+'
        found=false
        for commit in $(git log origin/${{ github.base_ref }}..HEAD --pretty=format:'%s'); do
          echo "Checking commit: $commit"
          if echo "$commit" | grep -qE "$regex"; then
            found=true
          fi
        done
        if [ "$found" = false ]; then
          echo "❌ At least one commit must contain a Jira ticket ID (e.g., PROJ-123)"
          exit 1
        fi
