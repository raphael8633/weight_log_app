from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, timedelta, datetime
import psycopg2
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)
print(f"DB_HOST={os.getenv('DB_HOST')}")
print(f"DB_NAME={os.getenv('DB_NAME')}")
print(f"DB_USER={os.getenv('DB_USER')}")
print(f"DB_PASSWORD={os.getenv('DB_PASSWORD')}")

app = FastAPI()

# ===== 靜態檔案設定 =====
app.mount("/static", StaticFiles(directory="static"), name="static")

# ===== Database Config =====
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# ===== Database Connect =====
def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

# ===== Pydantic Schemas =====
class WeightRecord(BaseModel):
    date: Optional[str] = None  # 接收字符串
    weight: float

class WeightResponse(BaseModel):
    date: date
    weight: Optional[float]

# ===== Routes =====

@app.post("/api/weights")
def add_weight(record: WeightRecord):
    if record.date:
        record_date = datetime.strptime(record.date, "%Y-%m-%d").date()
    else:
        record_date = date.today()

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO weight_records (record_date, weight)
            VALUES (%s, %s)
            ON CONFLICT (record_date) DO UPDATE
            SET weight = EXCLUDED.weight;
        """, (record_date, record.weight))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

    return {"status": "success", "message": "Weight recorded successfully."}

@app.get("/api/weights", response_model=List[WeightResponse])
def get_weights(days: int = Query(default=90, ge=1, le=365)):
    today = date.today()
    start_date = today - timedelta(days=days - 1)

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT record_date, weight
            FROM weight_records
            WHERE record_date BETWEEN %s AND %s;
        """, (start_date, today))
        rows = cur.fetchall()

        data_map = {r[0]: r[1] for r in rows}
        result = []

        for i in range(days):
            d = start_date + timedelta(days=i)
            result.append({
                "date": d,
                "weight": data_map.get(d)
            })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

    return result

@app.get("/api/weights/all", response_model=List[WeightResponse])
def get_all_weights():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT MIN(record_date) FROM weight_records;")
        min_row = cur.fetchone()
        start_date = min_row[0]

        if not start_date:
            return []

        today = date.today()

        cur.execute("""
            SELECT record_date, weight
            FROM weight_records
            WHERE record_date BETWEEN %s AND %s;
        """, (start_date, today))
        rows = cur.fetchall()

        data_map = {r[0]: r[1] for r in rows}
        delta = (today - start_date).days + 1
        result = []

        for i in range(delta):
            d = start_date + timedelta(days=i)
            result.append({
                "date": d,
                "weight": data_map.get(d)
            })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

    return result

@app.get("/api/weights/{record_date}", response_model=WeightResponse)
def get_weight_by_date(record_date: date):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT weight FROM weight_records WHERE record_date = %s;
        """, (record_date,))
        row = cur.fetchone()
        weight = row[0] if row else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

    return {"date": record_date, "weight": weight}