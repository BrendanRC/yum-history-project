#!/bin/bash
set -e

# Deploy infrastructure
cd yum-history-terraform
terraform init
terraform apply -auto-approve

# Get ECR repository URL
ECR_URL=$(terraform output -raw ecr_repository_url)

# Build and push Docker image
cd ../yum-history-frontend
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_URL
docker build -t yum-history-frontend .
docker tag yum-history-frontend:latest $ECR_URL:latest
docker push $ECR_URL:latest

# Update ECS service
aws ecs update-service --cluster yum-history-cluster --service yum-history-frontend --force-new-deployment

echo "Deployment complete!"
echo "ECR Repository: $ECR_URL"
