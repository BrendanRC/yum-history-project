#!/usr/bin/env python3
import sqlite3
import sys
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def query_dnf_history(db_path='/var/lib/dnf/history.sqlite'):
    if not os.path.exists(db_path):
        logger.error(f"Database file not found: {db_path}")
        return False
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, dt_begin, dt_end, cmdline, rpmdb_version_begin 
            FROM trans 
            ORDER BY id DESC 
            LIMIT 10
        """)
        
        print("Recent DNF Transactions:")
        print("-" * 80)
        for row in cursor.fetchall():
            tid, dt_begin, dt_end, cmdline, rpmdb_ver = row
            begin_time = datetime.fromtimestamp(dt_begin).strftime('%Y-%m-%d %H:%M:%S')
            print(f"ID: {tid} | {begin_time} | {cmdline}")
        
        print("\nPackage Operations:")
        print("-" * 80)
        cursor.execute("""
            SELECT ti.trans_id, ti.action, r.name, r.version, r.release, ti.state
            FROM trans_item ti
            JOIN rpm r ON ti.item_id = r.item_id
            ORDER BY ti.trans_id DESC
            LIMIT 20
        """)
        
        actions = {1: "INSTALL", 2: "UPGRADE", 3: "DOWNGRADE", 4: "REMOVE", 5: "REINSTALL", 6: "UPGRADE", 7: "UPGRADE"}
        
        for row in cursor.fetchall():
            trans_id, action, name, version, release, state = row
            action_name = actions.get(action, f"ACTION_{action}")
            print(f"TID: {trans_id} | {action_name} | {name}-{version}-{release}")
            
        conn.close()
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else '/var/lib/dnf/history.sqlite'
    success = query_dnf_history(db_path)
    sys.exit(0 if success else 1)
