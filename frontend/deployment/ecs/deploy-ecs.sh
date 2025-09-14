#!/bin/bash
set -e

echo "Deploying YUM History Frontend to ECS..."

# Deploy ECS infrastructure
terraform init
terraform apply -auto-approve

# Get ECR repository URL
ECR_URL=$(terraform output -raw ecr_repository_url)

# Build and push Docker image from project root
cd ../../
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_URL
docker build -f deployment/ecs/Dockerfile -t yum-history-frontend .
docker tag yum-history-frontend:latest $ECR_URL:latest
docker push $ECR_URL:latest

# Update ECS service
aws ecs update-service --cluster yum-history-cluster --service yum-history-frontend --force-new-deployment

echo "ECS deployment complete!"
echo "ECR Repository: $ECR_URL"
echo "Check AWS ECS console for the service public IP"
