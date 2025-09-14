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
    """Sync data from S3 to SQLite"""
    import socket
    from datetime import datetime
    bucket_name = os.environ.get('S3_BUCKET_NAME')
    server_id = os.environ.get('SERVER_ID', socket.gethostname())
    # Use current date for the path
    current_date = datetime.now().strftime('%Y/%m/%d')
    s3_key = os.environ.get('S3_KEY_PATH', f'servers/{server_id}/package-history/{current_date}/history.jsonl')
    
    if not bucket_name:
        return JsonResponse({'error': 'S3_BUCKET_NAME must be set'}, status=400)
    
    try:
        s3_client = boto3.client('s3')
        response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
        content = response['Body'].read().decode('utf-8')
        
        YumHistory.objects.all().delete()
        
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
        
        return JsonResponse({'message': 'Data synced successfully'})
    
    except Exception as e:
        logger.error(f"S3 sync error: {e}")
        return JsonResponse({'error': str(e)}, status=500)
