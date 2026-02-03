# Deployment Guide

## Overview

This guide covers deploying Unitree WebRTC Connect to production environments.

**Target Environments:**
- Cloud platforms (AWS, Azure, GCP)
- Docker containerization
- Kubernetes orchestration
- CI/CD automation

---

## Prerequisites

### System Requirements

- **Python:** 3.11 or higher
- **Operating System:** Linux (Ubuntu 22.04 LTS recommended)
- **Memory:** Minimum 2GB RAM (4GB recommended)
- **CPU:** 2+ cores recommended
- **Network:** Low-latency connection for WebRTC streaming

### Required Services

- **Database:** PostgreSQL 14+ (production) or SQLite (development)
- **Cache:** Redis 7+ for session management
- **Web Server:** Nginx or Apache for reverse proxy
- **SSL/TLS:** Valid SSL certificate for HTTPS

---

## Environment Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-secret-key-here  # Generate with: python -c "import secrets; print(secrets.token_hex(32))"

# Server Configuration
HOST=0.0.0.0
PORT=5000

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/unitree_webrtc
# Or for SQLite: DATABASE_URL=sqlite:///unitree_webrtc.db

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# WebRTC Configuration
WEBRTC_TIMEOUT=30
WEBRTC_MAX_CONNECTIONS=10

# Audio Configuration
AUDIO_SAMPLE_RATE=48000
AUDIO_CHANNELS=2
AUDIO_ENABLED=True

# Video Configuration
VIDEO_FRAME_QUEUE_SIZE=30
VIDEO_JPEG_QUALITY=85

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=/var/log/unitree_webrtc/app.log

# Security
ALLOWED_ORIGINS=https://yourdomain.com
CORS_ENABLED=True
```

### Security Best Practices

1. **Never commit `.env` files to version control**
2. **Use strong SECRET_KEY** (minimum 32 bytes)
3. **Enable HTTPS** in production
4. **Restrict CORS origins** to trusted domains
5. **Use environment-specific configurations**

---

## Docker Deployment

### Dockerfile

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    portaudio19-dev \
    libopencv-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create log directory
RUN mkdir -p /var/log/unitree_webrtc

# Expose port
EXPOSE 5000

# Run application
CMD ["python", "web_interface.py"]
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://postgres:password@db:5432/unitree_webrtc
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/var/log/unitree_webrtc
    restart: unless-stopped

  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=unitree_webrtc
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
```

### Build and Run

```bash
# Build Docker image
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f web

# Stop services
docker-compose down
```

---

## Cloud Deployment

### AWS Deployment (ECS + Fargate)

#### 1. Create ECR Repository

```bash
# Create ECR repository
aws ecr create-repository --repository-name unitree-webrtc-connect

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and push image
docker build -t unitree-webrtc-connect .
docker tag unitree-webrtc-connect:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/unitree-webrtc-connect:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/unitree-webrtc-connect:latest
```

#### 2. Create ECS Task Definition

Create `ecs-task-definition.json`:

```json
{
  "family": "unitree-webrtc-connect",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "web",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/unitree-webrtc-connect:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "FLASK_ENV", "value": "production"},
        {"name": "DATABASE_URL", "value": "postgresql://..."},
        {"name": "REDIS_URL", "value": "redis://..."}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/unitree-webrtc-connect",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### 3. Create ECS Service

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name unitree-webrtc-cluster

# Register task definition
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# Create service
aws ecs create-service \
  --cluster unitree-webrtc-cluster \
  --service-name unitree-webrtc-service \
  --task-definition unitree-webrtc-connect \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

### Azure Deployment (Container Instances)

```bash
# Login to Azure
az login

# Create resource group
az group create --name unitree-webrtc-rg --location eastus

# Create container registry
az acr create --resource-group unitree-webrtc-rg --name unitreewebrtcacr --sku Basic

# Build and push image
az acr build --registry unitreewebrtcacr --image unitree-webrtc-connect:latest .

# Deploy container instance
az container create \
  --resource-group unitree-webrtc-rg \
  --name unitree-webrtc-container \
  --image unitreewebrtcacr.azurecr.io/unitree-webrtc-connect:latest \
  --cpu 2 \
  --memory 4 \
  --ports 5000 \
  --environment-variables FLASK_ENV=production DATABASE_URL=postgresql://... \
  --dns-name-label unitree-webrtc
```

### GCP Deployment (Cloud Run)

```bash
# Login to GCP
gcloud auth login

# Set project
gcloud config set project your-project-id

# Build and push image
gcloud builds submit --tag gcr.io/your-project-id/unitree-webrtc-connect

# Deploy to Cloud Run
gcloud run deploy unitree-webrtc-connect \
  --image gcr.io/your-project-id/unitree-webrtc-connect \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars FLASK_ENV=production,DATABASE_URL=postgresql://...
```

---

## Nginx Configuration

Create `nginx.conf`:

```nginx
upstream unitree_webrtc {
    server web:5000;
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 100M;

    location / {
        proxy_pass http://unitree_webrtc;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /socket.io/ {
        proxy_pass http://unitree_webrtc;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Video streaming
    location /video_feed {
        proxy_pass http://unitree_webrtc;
        proxy_buffering off;
        proxy_cache off;
    }
}
```

---

## CI/CD Pipeline (GitHub Actions)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches:
      - master

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run tests
        run: pytest tests/ -v --cov=. --cov-fail-under=80

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1

      - name: Build and push Docker image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: unitree-webrtc-connect
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG

      - name: Deploy to ECS
        run: |
          aws ecs update-service --cluster unitree-webrtc-cluster --service unitree-webrtc-service --force-new-deployment
```

---

## Monitoring and Logging

### Application Logging

Configure logging in `web_interface.py`:

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
log_file = os.getenv('LOG_FILE', '/var/log/unitree_webrtc/app.log')
log_level = os.getenv('LOG_LEVEL', 'INFO')

handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=10)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))

logging.basicConfig(
    level=getattr(logging, log_level),
    handlers=[handler, logging.StreamHandler()]
)
```

### Health Check Endpoint

Add to `web_interface.py`:

```python
@app.route('/health')
def health_check():
    """Health check endpoint for load balancers."""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'connected': is_connected
    }), 200
```

---

## Troubleshooting

### Common Issues

**Issue:** WebRTC connection fails in production
- **Solution:** Ensure HTTPS is enabled (WebRTC requires secure context)
- **Solution:** Check firewall rules allow WebRTC ports (UDP 49152-65535)

**Issue:** Audio/video streaming not working
- **Solution:** Verify PyAudio and OpenCV are installed correctly
- **Solution:** Check system audio devices are available

**Issue:** High latency or dropped frames
- **Solution:** Increase server resources (CPU/memory)
- **Solution:** Optimize network configuration
- **Solution:** Reduce video quality or frame rate

---

## Production Checklist

- [ ] Environment variables configured
- [ ] SSL/TLS certificates installed
- [ ] Database migrations applied
- [ ] Redis cache configured
- [ ] Nginx reverse proxy configured
- [ ] Firewall rules configured
- [ ] Health check endpoint working
- [ ] Logging configured
- [ ] Monitoring set up
- [ ] Backup strategy implemented
- [ ] CI/CD pipeline tested
- [ ] Load testing completed
- [ ] Security audit performed

