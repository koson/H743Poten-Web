#!/bin/bash

# Add VS Code shell integration
if [ -f "$HOME/.vscode-server/bin/*/shellIntegration.bash" ]; then
    . "$HOME/.vscode-server/bin/*/shellIntegration.bash"
fi

# Set up environment variables
export PYTHONPATH="${PYTHONPATH}:/mnt/d/GitHubRepos/__Potentiostat/poten-2025/H743Poten/H743Poten-Web/src"
export PATH="$PATH:$HOME/.local/bin"

# Set up Python aliases
alias python=python3
alias pip=pip3

# Set up development aliases
alias dev='cd /mnt/d/GitHubRepos/__Potentiostat/poten-2025/H743Poten/H743Poten-Web && python3 auto_dev.py'
alias dev-start='dev start'
alias dev-stop='dev stop'
alias dev-restart='dev restart'
alias dev-logs='dev logs'

# Function to run development server
run_dev() {
    cd /mnt/d/GitHubRepos/__Potentiostat/poten-2025/H743Poten/H743Poten-Web/src && python3 run_dev.py
}

# Enable auto-cd
shopt -s autocd

# Better command history
HISTSIZE=10000
HISTFILESIZE=20000
shopt -s histappend
PROMPT_COMMAND="history -a;$PROMPT_COMMAND"

# Better completion
if [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
fi