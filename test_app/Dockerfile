FROM python:3.9-slim

WORKDIR /app

# Copy the entire root contents
COPY . /app/

# Install dependencies
RUN pip install --no-cache-dir pydantic

# Install oguild package (pyproject.toml is in root)
RUN pip install -e .

# Install guildpack alias package (pyproject.toml is in alias/)
RUN pip install -e ./alias

# Make sure log output is shown immediately
ENV PYTHONUNBUFFERED=1

CMD ["python", "test_app/main.py"]
