# Using venv (simplest)

python -m venv venv
source venv/bin/activate # or Windows equivalent

pip install \
httpx \
pytest \
fastapi \
uvicorn \
python-dotenv \
pydantic-settings \
pydantic \
anthropic \
google-genai

pip freeze > requirements.txt

# Create .gitignore file

echo "venv/" > .gitignore
echo "**pycache**/" >> .gitignore
echo ".env" >> .gitignore
