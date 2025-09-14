# YUM History Project Deployment Guide

## Prerequisites
- Python 3.9+
- Terraform
- AWS CLI configured
- Git with SSH keys

## Default: Local Deployment

### 1. Clone Repositories
```bash
git clone git@github.com:BrendanRC/yum-history-frontend.git
git clone git@github.com:BrendanRC/yum-history-app.git
git clone git@github.com:BrendanRC/yum-history-terraform.git
```

### 2. Deploy Infrastructure (First Time Only)
```bash
cd yum-history-terraform
terraform init
terraform apply
# Note: Creates shared bucket "yum-package-history-shared"
```

### 3. Setup Frontend
```bash
cd ../yum-history-frontend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
```

### 4. Upload Data
```bash
cd ../yum-history-app
export SERVER_ID=$(hostname)  # or custom server name
python3 upload_history_s3select.py yum-package-history-shared
```

### 5. Run Application
```bash
cd ../yum-history-frontend
source venv/bin/activate
export DEBUG=true
export S3_BUCKET_NAME=yum-package-history-shared
export SERVER_ID=$(hostname)  # or custom server name
python manage.py runserver 0.0.0.0:8000
```

## Alternative: ECS Deployment

### Prerequisites
- Docker installed
- AWS CLI configured with ECS permissions

### Deploy to ECS
```bash
cd yum-history-frontend/deployment/ecs
./deploy-ecs.sh
```

This creates:
- ECS Fargate cluster
- ECR repository
- VPC with public subnet
- Load balancer (optional)
- CloudWatch logging

Access via ECS task public IP on port 8000.

## Access
- **Local**: http://localhost:8000
- **ECS**: Check AWS ECS console for task public IP
- Use "Sync from S3" button to load data

## Environment Variables
- `DEBUG`: Set to `true` for development
- `S3_BUCKET_NAME`: Always `yum-package-history-shared`
- `SERVER_ID`: Unique identifier for this server (defaults to hostname)
- `DJANGO_SECRET_KEY`: Generate for production

## Multi-Server Setup
Each server stores data under `servers/{SERVER_ID}/` in the shared bucket:
```
s3://yum-package-history-shared/
├── servers/
│   ├── web-server-01/package-history/...
│   ├── db-server-02/package-history/...
│   └── app-server-03/package-history/...
```
