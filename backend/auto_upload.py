#!/usr/bin/env python3
"""
Automated yum history uploader - designed to run as a cron job
Uploads yum history to S3 whenever there are new transactions
"""
import sqlite3
import json
import boto3
import os
import sys
import logging
from datetime import datetime
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_latest_transaction_id(db_path='/var/lib/dnf/history.sqlite'):
    """Get the ID of the most recent transaction"""
    if not os.path.exists(db_path):
        return None
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT MAX(id) FROM trans')
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except sqlite3.Error:
        return None

def check_if_upload_needed(bucket_name, server_id):
    """Check if we need to upload by comparing latest transaction ID"""
    try:
        s3 = boto3.client('s3')
        
        # Try to get the metadata of the latest upload
        key = f"servers/{server_id}/package-history/latest_transaction_id"
        try:
            response = s3.get_object(Bucket=bucket_name, Key=key)
            last_uploaded_id = int(response['Body'].read().decode('utf-8').strip())
        except:
            last_uploaded_id = 0
        
        current_id = get_latest_transaction_id()
        if current_id is None:
            return False
            
        return current_id > last_uploaded_id
        
    except Exception as e:
        logger.error(f"Error checking upload status: {e}")
        return True  # Upload on error to be safe

def upload_transaction_id(bucket_name, server_id, transaction_id):
    """Store the latest transaction ID in S3"""
    try:
        s3 = boto3.client('s3')
        key = f"servers/{server_id}/package-history/latest_transaction_id"
        s3.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=str(transaction_id),
            ContentType='text/plain'
        )
    except Exception as e:
        logger.error(f"Error storing transaction ID: {e}")

def main():
    bucket_name = os.environ.get('S3_BUCKET_NAME', 'package-history-3ddh4rp4')
    server_id = os.environ.get('SERVER_ID', os.uname().nodename)
    
    # Check if upload is needed
    if not check_if_upload_needed(bucket_name, server_id):
        logger.info("No new transactions, skipping upload")
        return
    
    # Run the main upload script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    upload_script = os.path.join(script_dir, 'upload_history_to_s3.py')
    
    import subprocess
    result = subprocess.run([
        sys.executable, upload_script, bucket_name
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        # Update the transaction ID marker
        latest_id = get_latest_transaction_id()
        if latest_id:
            upload_transaction_id(bucket_name, server_id, latest_id)
        logger.info("Upload completed successfully")
    else:
        logger.error(f"Upload failed: {result.stderr}")
        sys.exit(1)

if __name__ == "__main__":
    main()
