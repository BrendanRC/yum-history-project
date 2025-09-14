from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import YumHistory
import boto3
import json
import os
import logging

logger = logging.getLogger(__name__)

def index(request):
    return render(request, 'history/index.html')

def get_yum_history(request):
    try:
        records = YumHistory.objects.all().values(
            'transaction_id', 'timestamp', 'command', 'user_id', 'action', 
            'package_name', 'package_version', 'package_arch'
        )
        return JsonResponse({'data': list(records)})
    
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def sync_from_s3(request):
    """Sync data from S3 to SQLite - dynamically find latest data"""
    bucket_name = os.environ.get('S3_BUCKET_NAME')
    
    if not bucket_name:
        return JsonResponse({'error': 'S3_BUCKET_NAME must be set'}, status=400)
    
    try:
        s3_client = boto3.client('s3')
        
        # List all objects in the bucket to find the latest history file
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix='servers/'
        )
        
        if 'Contents' not in response:
            return JsonResponse({'error': 'No history files found in S3'}, status=404)
        
        # Find the most recent history file
        latest_file = None
        latest_time = None
        
        for obj in response['Contents']:
            key = obj['Key']
            if key.endswith(('.json', '.jsonl')) and 'history' in key:
                if latest_time is None or obj['LastModified'] > latest_time:
                    latest_file = key
                    latest_time = obj['LastModified']
        
        if not latest_file:
            return JsonResponse({'error': 'No history files found'}, status=404)
        
        logger.info(f"Using latest file: {latest_file}")
        
        # Get the file content
        response = s3_client.get_object(Bucket=bucket_name, Key=latest_file)
        content = response['Body'].read().decode('utf-8')
        
        # Clear existing data
        YumHistory.objects.all().delete()
        
        # Handle both JSON and JSONL formats
        if latest_file.endswith('.json'):
            # JSON format - array of transactions
            data = json.loads(content)
            for transaction in data:
                for package in transaction.get('packages', []):
                    YumHistory.objects.create(
                        transaction_id=transaction.get('transaction_id', ''),
                        timestamp=transaction.get('timestamp', ''),
                        command=transaction.get('command', ''),
                        user_id=transaction.get('user_id', ''),
                        package_name=package.get('name', ''),
                        package_version=package.get('version', ''),
                        package_arch=package.get('arch', ''),
                        action=package.get('action', 0)
                    )
        else:
            # JSONL format - one record per line
            for line in content.strip().split('\n'):
                if line:
                    record = json.loads(line)
                    YumHistory.objects.create(
                        transaction_id=record.get('transaction_id', ''),
                        timestamp=record.get('timestamp', ''),
                        command=record.get('command', ''),
                        user_id=record.get('user_id', ''),
                        package_name=record.get('package_name', ''),
                        package_version=record.get('package_version', ''),
                        package_arch=record.get('package_arch', ''),
                        action=record.get('action', 0)
                    )
        
        return JsonResponse({
            'message': f'Data synced successfully from {latest_file}',
            'file': latest_file,
            'last_modified': latest_time.isoformat()
        })
    
    except Exception as e:
        logger.error(f"S3 sync error: {e}")
        return JsonResponse({'error': str(e)}, status=500)
