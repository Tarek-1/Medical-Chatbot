#!/bin/bash

# Create core project structure
mkdir -p src
mkdir -p data
mkdir -p research
mkdir -p templates
mkdir -p static

# Create Python module files inside src/
touch src/__init__.py
touch src/config.py
touch src/data_loader.py
touch src/retriever.py
touch src/llm_interface.py
touch src/prompts.py
touch src/chatbot.py

# Create frontend files
touch templates/index.html
touch static/style.css
touch static/script.js

# Create root-level project files
touch app.py
touch .env
touch setup.py
touch requirements.txt
touch README.md
touch LICENSE

# Create research notebook
touch research/trials.ipynb

# Display structure summary
echo "Directory structure created:"
