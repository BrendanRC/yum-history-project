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
        
        # Try to get user info, fallback if column doesn't exist
        try:
            cursor.execute('''
                SELECT t.id, t.dt_begin, t.cmdline, t.loginuid,
                       ti.action, r.name, r.version, r.release, r.arch
                FROM trans t
                LEFT JOIN trans_item ti ON t.id = ti.trans_id
                LEFT JOIN rpm r ON ti.item_id = r.item_id
                ORDER BY t.dt_begin DESC
            ''')
        except sqlite3.OperationalError:
            # Fallback if loginuid column doesn't exist
            cursor.execute('''
                SELECT t.id, t.dt_begin, t.cmdline, NULL as loginuid,
                       ti.action, r.name, r.version, r.release, r.arch
                FROM trans t
                LEFT JOIN trans_item ti ON t.id = ti.trans_id
                LEFT JOIN rpm r ON ti.item_id = r.item_id
                ORDER BY t.dt_begin DESC
            ''')
        
        jsonl_lines = []
        for row in cursor.fetchall():
            trans_id, timestamp, cmdline, loginuid, action, name, version, release, arch = row
            
            if name:
                # Use current user if loginuid is null (WSL compatibility)
                user_info = loginuid if loginuid is not None else os.getenv('USER', 'unknown')
                record = {
                    'transaction_id': trans_id,
                    'timestamp': datetime.fromtimestamp(timestamp).isoformat(),
                    'command': cmdline,
                    'user_id': user_info,
                    'package_name': name,
                    'package_version': f"{version}-{release}",
                    'package_arch': arch,
                    'action': action
                }
                jsonl_lines.append(json.dumps(record))
        
        conn.close()
        return '\n'.join(jsonl_lines)
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return None

def upload_to_s3(bucket_name, history_jsonl):
    if not history_jsonl:
        logger.error("No history data to upload")
        return None
        
    try:
        import socket
        s3 = boto3.client('s3')
        server_id = os.environ.get('SERVER_ID', socket.gethostname())
        key = f"servers/{server_id}/package-history/{datetime.now().strftime('%Y/%m/%d')}/history.jsonl"
        
        s3.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=history_jsonl,
            ContentType='application/x-jsonlines'
        )
        
        logger.info(f"Uploaded to s3://{bucket_name}/{key}")
        return key
        
    except ClientError as e:
        logger.error(f"S3 upload error: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 upload_history_s3select.py <bucket-name> [db-path]")
        sys.exit(1)
    
    bucket_name = sys.argv[1]
    db_path = sys.argv[2] if len(sys.argv) > 2 else '/var/lib/dnf/history.sqlite'
    
    history_jsonl = get_package_history(db_path)
    key = upload_to_s3(bucket_name, history_jsonl)
    sys.exit(0 if key else 1)
