#!/bin/bash

# Script to check and setup .env file
# Can be run standalone or called from deploy.sh

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

print_prompt() {
    echo -e "${BLUE}? $1${NC}"
}

# Check if .env exists
if [ -f ".env" ]; then
    print_success ".env file already exists"
    
    # Ask if user wants to update it
    print_prompt "Do you want to update .env from a template? (y/n)"
    read -r response
    
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        print_info "Keeping existing .env file"
        exit 0
    fi
fi

# List available env templates
echo ""
print_info "Available environment templates:"
echo ""

ENV_FILES=()
counter=1

# Check for .env.example
if [ -f ".env.example" ]; then
    echo "  [$counter] .env.example (default template)"
    ENV_FILES+=(".env.example")
    ((counter++))
fi

# Check for .env.prod
if [ -f ".env.prod" ]; then
    echo "  [$counter] .env.prod (production)"
    ENV_FILES+=(".env.prod")
    ((counter++))
fi

# Check for .env.dev
if [ -f ".env.dev" ]; then
    echo "  [$counter] .env.dev (development)"
    ENV_FILES+=(".env.dev")
    ((counter++))
fi

# Check for .env.local
if [ -f ".env.local" ]; then
    echo "  [$counter] .env.local (local)"
    ENV_FILES+=(".env.local")
    ((counter++))
fi

# Check for other .env.* files
for file in .env.*; do
    if [ -f "$file" ] && [[ ! "$file" =~ \.(example|prod|dev|local)$ ]]; then
        echo "  [$counter] $file"
        ENV_FILES+=("$file")
        ((counter++))
    fi
done

echo "  [0] Create empty .env file"
echo ""

# If no templates found, create from .env.example or empty
if [ ${#ENV_FILES[@]} -eq 0 ]; then
    print_info "No environment templates found. Creating empty .env file..."
    touch .env
    print_success ".env file created (empty)"
    print_info "Please edit .env and add your configuration"
    exit 0
fi

# Ask user to choose
print_prompt "Choose a template (0-$((counter-1))):"
read -r choice

# Validate choice
if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 0 ] || [ "$choice" -ge "$counter" ]; then
    print_info "Invalid choice. Using .env.example as default"
    choice=1
fi

# Create .env file
if [ "$choice" -eq 0 ]; then
    touch .env
    print_success ".env file created (empty)"
    print_info "Please edit .env and add your configuration"
else
    selected_file="${ENV_FILES[$((choice-1))]}"
    cp "$selected_file" .env
    print_success ".env file created from $selected_file"
fi

# Show what's in the .env file (without sensitive values)
echo ""
print_info "Current .env configuration:"
echo ""
while IFS= read -r line; do
    # Skip empty lines and comments
    if [[ -z "$line" ]] || [[ "$line" =~ ^[[:space:]]*# ]]; then
        continue
    fi
    
    # Show key but hide value
    if [[ "$line" =~ ^([^=]+)=(.*)$ ]]; then
        key="${BASH_REMATCH[1]}"
        value="${BASH_REMATCH[2]}"
        
        if [ -z "$value" ]; then
            echo "  $key = (empty)"
        else
            echo "  $key = ***"
        fi
    fi
done < .env

echo ""
print_info "Remember to edit .env with your actual values if needed"
