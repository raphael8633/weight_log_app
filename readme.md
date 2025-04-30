# 📱 個人體重追蹤 Web App（FastAPI + Chart.js）

這是一個簡潔、行動優化的個人專屬體重追蹤系統，支援每日輸入體重、自動補缺漏日期、體重視覺化圖表，以及多日均線分析（7/14/30 日均線）。

---

## 📁 專案結構

```
my-weight-app/
├── main.py                  # FastAPI 主程式（含所有 API）
├── static/
│   └── chart.html          # 前端頁面：輸入體重與顯示圖表
├── .env                    # 環境變數檔（資料庫設定）
├── requirements.txt        # Python 套件清單
└── venv/                   # 虛擬環境（可選）
```

---

## 🚀 安裝與啟動

### 1️⃣ 建立虛擬環境（不污染系統 Python）

```bash
python3 -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
```

### 2️⃣ 安裝套件

```bash
pip install -r requirements.txt
```

### 3️⃣ 建立 `.env` 檔案

在根目錄下新增 `.env` 檔，填入：

```
DB_HOST=localhost
DB_NAME=your_db_name
DB_USER=your_username
DB_PASSWORD=your_password
```

### 4️⃣ 建立資料庫表格（PostgreSQL）

```sql
CREATE TABLE weight_records (
    id SERIAL PRIMARY KEY,
    record_date DATE NOT NULL UNIQUE,
    weight DECIMAL(5,2) NOT NULL
);

CREATE INDEX idx_weight_record_date ON weight_records(record_date);
```

### 5️⃣ 啟動伺服器

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

瀏覽器開啟：`http://your-ip:8000/static/chart.html`

API 文件（Swagger UI）：`http://your-ip:8000/docs`

---

## ✅ 功能特色

- ✅ 體重輸入（支援補登任意日期）
- ✅ 自動記錄日期、不重複寫入
- ✅ 自動補空白天數為 null（視覺上持續）
- ✅ Chart.js 畫出體重曲線
- ✅ 顯示 7、14、30 日均線
- ✅ 切換顯示範圍（7 / 14 / 30 / 全部）
- ✅ 顯示當前體重與平均摘要資訊

---

## 📦 部署建議（非 Docker）

1. 上傳到 DigitalOcean Droplet
2. 建立虛擬環境、安裝依賴
3. 使用 `systemd` 或 `tmux` 啟動 uvicorn
4. 用 nginx 反向代理 `/static` 和 `/api`

如需協助部署指令與 nginx 設定，可聯絡作者或查閱說明。

---

> Made with ❤️ by ChatGPT and your data
