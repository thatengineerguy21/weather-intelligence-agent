FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toolbox binary and config
COPY mcp-toolbox/toolbox ./toolbox
COPY mcp-toolbox/tools.yaml ./tools.yaml

# Copy application code
COPY main.py .
COPY weather_agent_app/ ./weather_agent_app/

# Startup script will run both toolbox and the agent server
COPY start.sh .
RUN chmod +x start.sh

ENV PORT=8080
EXPOSE 8080

CMD ["./start.sh"]