#!/usr/bin/env python3
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

def get_package_history(db_path='/var/lib/dnf/history.sqlite'):
    if not os.path.exists(db_path):
        logger.error(f"Database file not found: {db_path}")
        return None
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT t.id, t.dt_begin, t.cmdline,
                   ti.action, r.name, r.version, r.release, r.arch
            FROM trans t
            LEFT JOIN trans_item ti ON t.id = ti.trans_id
            LEFT JOIN rpm r ON ti.item_id = r.item_id
            ORDER BY t.dt_begin DESC
        ''')
        
        transactions = {}
        for row in cursor.fetchall():
            trans_id, timestamp, cmdline, action, name, version, release, arch = row
            
            if trans_id not in transactions:
                transactions[trans_id] = {
                    'transaction_id': trans_id,
                    'timestamp': datetime.fromtimestamp(timestamp).isoformat(),
                    'command': cmdline,
                    'user_id': 'root',
                    'packages': []
                }
            
            if name:
                transactions[trans_id]['packages'].append({
                    'name': name,
                    'version': f"{version}-{release}",
                    'arch': arch,
                    'action': action
                })
        
        conn.close()
        return list(transactions.values())
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return None

def upload_to_s3(bucket_name, history):
    if not history:
        logger.error("No history data to upload")
        return False
        
    try:
        import socket
        s3 = boto3.client('s3')
        server_id = os.environ.get('SERVER_ID', socket.gethostname())
        key = f"servers/{server_id}/package-history/{datetime.now().strftime('%Y/%m/%d')}/history.json"
        
        s3.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=json.dumps(history, indent=2),
            ContentType='application/json'
        )
        
        logger.info(f"Uploaded to s3://{bucket_name}/{key}")
        return True
        
    except ClientError as e:
        logger.error(f"S3 upload error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 upload_history_to_s3.py <bucket-name> [db-path]")
        sys.exit(1)
    
    bucket_name = sys.argv[1]
    db_path = sys.argv[2] if len(sys.argv) > 2 else '/var/lib/dnf/history.sqlite'
    
    history = get_package_history(db_path)
    success = upload_to_s3(bucket_name, history)
    sys.exit(0 if success else 1)
