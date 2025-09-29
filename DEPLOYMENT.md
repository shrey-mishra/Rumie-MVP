# RumieAI Phase II - Deployment Guide

This guide covers deploying the RumieAI Phase II backend to production environments.

## 🚀 Quick Deployment

### 1. Environment Setup

#### Required Environment Variables
Create a `.env` file with the following variables:

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/rumieai
SQLITE_DB_PATH=rumie.db

# Security Configuration
SECRET_KEY=your_super_secret_key_change_in_production_12345
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Configuration
GEMINI_API_KEY=your_actual_gemini_api_key_here
API_V1_STR=/v1

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10

# CORS Configuration
ALLOWED_ORIGINS=https://rumieai.com,https://app.rumieai.com
ALLOWED_METHODS=GET,POST,PUT,DELETE,OPTIONS
ALLOWED_HEADERS=Authorization,Content-Type,X-Requested-With

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Environment
ENVIRONMENT=production
DEBUG=False
```

### 2. Database Setup

#### PostgreSQL (Production)
```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb rumieai

# Update DATABASE_URL in .env
DATABASE_URL=postgresql://username:password@localhost:5432/rumieai
```

#### Run Migrations
```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head
```

### 3. Redis Setup

#### Install Redis
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Start Redis
redis-server
```

### 4. Application Deployment

#### Using Uvicorn (Development/Testing)
```bash
# Install dependencies
pip install -r requirements.txt

# Run application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Using Gunicorn (Production)
```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### Using Docker (Recommended)

Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/rumieai
      - REDIS_URL=redis://redis:6379/0
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=rumieai
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

Deploy with Docker:
```bash
# Build and start services
docker-compose up -d

# Run migrations
docker-compose exec app alembic upgrade head

# Check logs
docker-compose logs -f app
```

### 5. Cloud Deployment

#### Heroku Deployment

Create `Procfile`:
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Create `runtime.txt`:
```
python-3.10.11
```

Deploy to Heroku:
```bash
# Install Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# Login to Heroku
heroku login

# Create Heroku app
heroku create rumieai-backend

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:hobby-dev

# Add Redis addon
heroku addons:create heroku-redis:hobby-dev

# Set environment variables
heroku config:set GEMINI_API_KEY=your_gemini_api_key
heroku config:set SECRET_KEY=your_secret_key
heroku config:set ENVIRONMENT=production

# Deploy
git push heroku main

# Run migrations
heroku run alembic upgrade head
```

#### AWS Deployment

Using AWS Elastic Beanstalk:

1. Create `requirements.txt` (already exists)
2. Create `.ebextensions/01_packages.config`:
```yaml
packages:
  yum:
    postgresql-devel: []
    gcc: []
```

3. Deploy:
```bash
# Install EB CLI
pip install awsebcli

# Initialize EB
eb init

# Create environment
eb create production

# Deploy
eb deploy
```

#### Google Cloud Platform

Using Cloud Run:

1. Create `cloudbuild.yaml`:
```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/rumieai-backend', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/rumieai-backend']
  - name: 'gcr.io/cloud-builders/gcloud'
    args: ['run', 'deploy', 'rumieai-backend', '--image', 'gcr.io/$PROJECT_ID/rumieai-backend', '--platform', 'managed', '--region', 'us-central1']
```

2. Deploy:
```bash
# Build and deploy
gcloud builds submit --config cloudbuild.yaml
```

### 6. Monitoring and Logging

#### Health Checks
The application includes health check endpoints:
- `GET /health` - Application health
- `GET /` - Basic status

#### Logging
Structured logging is configured with:
- JSON format for production
- Request/response tracking
- Error monitoring
- Performance metrics

#### Monitoring Setup
```bash
# Install monitoring tools
pip install sentry-sdk[fastapi]

# Add to main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="your_sentry_dsn",
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
)
```

### 7. Security Checklist

- ✅ Environment variables secured
- ✅ CORS configured for production domains
- ✅ Rate limiting enabled
- ✅ Input validation with Pydantic
- ✅ Database connection secured
- ✅ Redis authentication (if needed)
- ✅ HTTPS enforced in production
- ✅ API keys protected
- ✅ Error handling without information leakage

### 8. Performance Optimization

#### Database Optimization
```python
# Add connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30
)
```

#### Caching
```python
# Add Redis caching for frequently accessed data
import redis
from functools import wraps

redis_client = redis.Redis.from_url(REDIS_URL)

def cache_result(expiry=3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, expiry, json.dumps(result))
            return result
        return wrapper
    return decorator
```

### 9. Backup and Recovery

#### Database Backup
```bash
# PostgreSQL backup
pg_dump -h localhost -U postgres rumieai > backup.sql

# Restore
psql -h localhost -U postgres rumieai < backup.sql
```

#### Automated Backups
```bash
# Create backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U postgres rumieai > "backup_${DATE}.sql"
aws s3 cp "backup_${DATE}.sql" s3://rumieai-backups/
```

### 10. Scaling Considerations

#### Horizontal Scaling
- Use load balancer (nginx, HAProxy)
- Multiple application instances
- Shared Redis for session storage
- Database read replicas

#### Vertical Scaling
- Increase server resources
- Optimize database queries
- Add caching layers
- Monitor performance metrics

## 🔧 Development vs Production

### Development
- SQLite database
- Mock Redis
- Debug mode enabled
- Local CORS origins
- Mock Gemini responses

### Production
- PostgreSQL database
- Real Redis instance
- Debug mode disabled
- Restricted CORS origins
- Real Gemini API integration
- HTTPS enforcement
- Monitoring and logging

## 📊 Performance Targets

- **Response Time**: < 200ms for 95% of requests
- **Throughput**: 1000+ requests/minute
- **Concurrent Users**: 100-200 users
- **Uptime**: 99.9% availability
- **Error Rate**: < 0.1%

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check DATABASE_URL format
   - Verify database is running
   - Check network connectivity

2. **Redis Connection Errors**
   - Verify REDIS_URL
   - Check Redis server status
   - Test connection manually

3. **Rate Limiting Issues**
   - Check rate limit configuration
   - Verify client IP detection
   - Review slowapi settings

4. **CORS Errors**
   - Verify ALLOWED_ORIGINS
   - Check preflight requests
   - Test with different browsers

### Monitoring Commands
```bash
# Check application logs
docker-compose logs -f app

# Check database connections
docker-compose exec db psql -U postgres -d rumieai -c "SELECT * FROM pg_stat_activity;"

# Check Redis
docker-compose exec redis redis-cli info

# Check application health
curl http://localhost:8000/health
```

---

**Deployment Complete!** 🎉

Your RumieAI Phase II backend is now ready for production with:
- ✅ Scalable architecture
- ✅ Security measures
- ✅ Monitoring setup
- ✅ Performance optimization
- ✅ Backup strategies
