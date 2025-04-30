from fastapi import FastAPI, HTTPException, Request, Form, Depends, Response, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasicCredentials
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

# ===== Database Config =====
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static")

# ===== Session 驗證函式 =====
def verify_session(request: Request):
    if request.cookies.get("session") != DB_PASSWORD:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

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
    date: Optional[str] = None
    weight: float

class WeightResponse(BaseModel):
    date: date
    weight: Optional[float]

# ===== Routes =====
@app.get("/", response_class=HTMLResponse)
def serve_chart(request: Request):
    if request.cookies.get("session") != DB_PASSWORD:
        return RedirectResponse("/login")
    with open("static/chart.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(request: Request, response: Response, username: str = Form(...), password: str = Form(...)):
    if username == DB_USER and password == DB_PASSWORD:
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie("session", password, httponly=True)
        return response
    return HTMLResponse("<h3>登入失敗</h3><a href='/login'>再試一次</a>", status_code=401)

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("session")
    return response

@app.post("/api/weights")
def add_weight(record: WeightRecord, request: Request):
    verify_session(request)
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
def get_weights(request: Request, days: int = Query(default=90, ge=1, le=365)):
    verify_session(request)
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
            result.append({"date": d, "weight": data_map.get(d)})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

    return result

@app.get("/api/weights/all", response_model=List[WeightResponse])
def get_all_weights(request: Request):
    verify_session(request)
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
            result.append({"date": d, "weight": data_map.get(d)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

    return result

@app.get("/api/weights/{record_date}", response_model=WeightResponse)
def get_weight_by_date(record_date: date, request: Request):
    verify_session(request)
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT weight FROM weight_records WHERE record_date = %s;", (record_date,))
        row = cur.fetchone()
        weight = row[0] if row else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

    return {"date": record_date, "weight": weight}