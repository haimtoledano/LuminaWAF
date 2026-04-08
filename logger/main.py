import os
import json
import time
import threading
import traceback
from datetime import datetime, timedelta
from dateutil.parser import parse as parse_date
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://waf_admin:waf_password@db:5432/waf_db")
LOG_FILE = "/app/envoy-dynamic/access.log"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def retention_worker():
    while True:
        try:
            with SessionLocal() as db:
                print("[Retention] Running retention policy check...", flush=True)
                # Fetch all VS
                servers = db.execute(text("SELECT id, log_retention_days FROM virtual_servers")).fetchall()
                for server in servers:
                    vs_id = server[0]
                    retention_days = server[1] or 7 # Default to 7 if null
                    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
                    
                    # Delete old logs for this VS
                    deleted = db.execute(
                        text("DELETE FROM access_logs WHERE vs_id = :vs_id AND timestamp < :cutoff"),
                        {"vs_id": vs_id, "cutoff": cutoff_date}
                    ).rowcount
                    db.commit()
                    if deleted > 0:
                        print(f"[Retention] Deleted {deleted} logs for VS {vs_id} (Older than {retention_days} days)", flush=True)
                        
        except Exception as e:
            print(f"[Retention] Error in retention worker: {e}", flush=True)
            traceback.print_exc()
        
        # Run every 10 minutes
        time.sleep(600)

def tail_logs():
    print(f"[Logger] Waiting for {LOG_FILE} to exist...", flush=True)
    while not os.path.exists(LOG_FILE):
        time.sleep(2)
        
    print(f"[Logger] Started tailing {LOG_FILE}", flush=True)
    with open(LOG_FILE, 'r') as f:
        # Go to the end of file (or we could read from start if we want to ingest missed logs)
        f.seek(0, os.SEEK_END)
        
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.5)
                continue
                
            line = line.strip()
            if not line:
                continue
                
            try:
                log_entry = json.loads(line)
                process_log_entry(log_entry)
            except json.JSONDecodeError:
                print(f"[Logger] Failed to decode JSON: {line}", flush=True)
            except Exception as e:
                print(f"[Logger] Error processing log: {e}", flush=True)

def process_log_entry(entry):
    server_name = entry.get("server")
    if not server_name:
        return
        
    with SessionLocal() as db:
        # Find VS ID by name
        res = db.execute(text("SELECT id FROM virtual_servers WHERE name = :name LIMIT 1"), {"name": server_name}).fetchone()
        vs_id = res[0] if res else server_name
        
        # Parse timestamp safely
        try:
            timestamp = parse_date(entry.get("time"))
        except:
            timestamp = datetime.utcnow()
            
        status_code = entry.get("status")
        try:
            status_code = int(status_code)
        except:
            status_code = 0
            
        req_body = entry.get("req_body")
        resp_body = entry.get("resp_body")
        
        # Truncate payloads to 10kb
        if req_body and len(req_body) > 10240:
            req_body = req_body[:10240] + "\n...[TRUNCATED]"
        if resp_body and len(resp_body) > 10240:
            resp_body = resp_body[:10240] + "\n...[TRUNCATED]"

        # Insert into access_logs
        db.execute(
            text("""
            INSERT INTO access_logs (id, vs_id, timestamp, method, path, status_code, client_ip, user_agent, req_payload, resp_payload, block_reason)
            VALUES (:id, :vs_id, :ts, :method, :path, :status, :ip, :ua, :req, :resp, :reason)
            """),
            {
                "id": str(os.urandom(16).hex()),
                "vs_id": vs_id,
                "ts": timestamp,
                "method": entry.get("method") or "UNKNOWN",
                "path": entry.get("path") or "/",
                "status": status_code,
                "ip": entry.get("client_ip") or "0.0.0.0",
                "ua": entry.get("user_agent") or "Unknown",
                "req": req_body,
                "resp": resp_body,
                "reason": entry.get("details")
            }
        )
        db.commit()

if __name__ == "__main__":
    time.sleep(5) # Wait for DB to be up
    
    # Start retention worker thread
    t = threading.Thread(target=retention_worker, daemon=True)
    t.start()
    
    # Start tailing logs
    tail_logs()
