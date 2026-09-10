# Self-Broker

Thu âm livestream broker (TikTok) → STT (Groq Whisper) → phân tích (Groq LLM), điều phối hoàn toàn bằng **Supabase Postgres** (state machine), không queue.

## Kiến trúc

```text
        ┌─────────────────┐
        │    FastAPI      │  api   (health, sources CRUD, pipeline views)
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │    Supabase     │  PostgreSQL (state machine) + Storage (audio)
        └───┬────────┬────┘
            │        │
   ┌────────▼──┐  ┌──▼────────┐  ┌──────────┐
   │ scanner   │  │ capture   │  │   stt    │
   │ detect    │  │ ffmpeg    │  │ whisper  │
   │ live      │─▶│ segments  │─▶│ + groq   │
   └───────────┘  └───────────┘  │   llm    │
                                 └──────────┘
```

- **scanner** — poll `sources`, resolve stream URL TikTok đang live, tạo `live_sessions` (DISCOVERED). Đồng thời chạy recovery sweep: chunk PROCESSING quá hạn → PENDING, worker chết → session về DISCOVERED, session ENDED đủ điều kiện → COMPLETED.
- **capture** — claim session `DISCOVERED` bằng `FOR UPDATE SKIP LOCKED`, cắt audio bằng ffmpeg (mặc định 300s/chunk), upload Supabase Storage, insert `audio_chunks` (PENDING).
- **stt** — claim chunk `PENDING`, transcribe qua Groq Whisper, lưu `transcripts`, phân tích LLM (tuỳ chọn), đánh dấu COMPLETED.
- **api** — FastAPI: `/health`, sources CRUD, view sessions/chunks/transcripts/jobs/workers cho console sau này.

Không Redis, không Kafka, không Celery. Các worker claim job bằng transaction:

```sql
SELECT * FROM audio_chunks
WHERE status = 'PENDING'
ORDER BY created_at
FOR UPDATE SKIP LOCKED
LIMIT 1;
```

## Cấu trúc

```text
app/
├── config.py        # env + settings
├── db.py            # Postgres helpers + claim_session / claim_chunk
├── storage.py       # Supabase Storage upload/download
├── telegram.py      # notifier
├── heartbeat.py     # workers registry (dead-worker detection)
├── tiktok.py        # resolve live stream URL (yt-dlp + curl_cffi)
├── scanner/         # python -m app.scanner
├── capture/         # python -m app.capture
├── stt/             # python -m app.stt
 └── api/             # uvicorn app.api.main:app
     └── console/     # dashboard UI phục vụ tại /console
supabase/migrations/ # schema + claim/recovery functions
```

## Console

Dashboard telemetry phục vụ ngay từ API, không cần build:

- Local: <http://localhost:8000/console> (gõ `/` cũng tự redirect)
- Render: `https://<api-service>.onrender.com/console`

Có: counters pipeline (sources / capturing / pending / processing / failed / transcripts),
bảng workers (cảnh báo đỏ khi heartbeat quá hạn >90s), bảng live sessions (filter theo
status) + progress chunks, panel detail (chunks + transcripts + analysis), jobs audit
trail, quản lý sources (add / stop / delete), tìm kiếm keyword trong transcripts,
nghe lại audio từng chunk (signed URL từ Supabase Storage), xem/copy merged transcript,
retry chunk FAILED → PENDING, trigger recovery sweep thủ công. Poll tự động mỗi 5s,
phím `R` refresh ngay, `Esc` đóng panel/modal.

## Chạy local

```bash
python3 -m venv ~/.venv && source ~/.venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # điền giá trị

# migrate (lần đầu / khi đổi schema)
psql "$DATABASE_URL" -f supabase/migrations/20260910000000_pipeline_schema.sql

python -m app.scanner   # terminal 1
python -m app.capture   # terminal 2
python -m app.stt       # terminal 3
uvicorn app.api.main:app --port 8000   # terminal 4
```

## Console (trang độc lập)

`console/index.html` là trang tĩnh độc lập — không cần backend phục vụ nó, gọi thẳng tới API (local hoặc Render):

1. Mở file (double-click) hoặc host tĩnh bất kỳ đâu (Render Static Site / GitHub Pages / Vercel)
2. Vào **Cài đặt** → nhập API base URL (VD `https://self-broker-api.onrender.com`) + Console token → Lưu (lưu localStorage)
3. Nếu API đặt biến `CONSOLE_TOKEN` thì mọi request phải kèm token (header `X-Console-Token`); `/health` luôn mở cho health check

## Deploy (Render)

`render.yaml` khai báo 5 service: `console` (static) + `api` (web) + `scanner` / `capture` / `stt` (worker), chung một Docker image cho các service Python, secrets để `sync: false` (điền trong Render Dashboard).

- API trên Render đặt `WORKER_CONTROL=0` — worker là service riêng của Render, không điều khiển start/stop qua API
- Đặt `CONSOLE_TOKEN` (chuỗi bí mật tùy ý) trên API và điền cùng giá trị vào Console → Cài đặt
- Sau khi deploy, mở URL của `self-broker-console` → Cài đặt → dán URL của `self-broker-api`

## State machines

```text
live_sessions : DISCOVERED → CAPTURING → ENDED → COMPLETED
                          ↘ FAILED (no audio / abandoned / capture error)
audio_chunks  : PENDING → PROCESSING → COMPLETED | FAILED
```

Recovery: heartbeat 15s vào bảng `workers`; scanner định kỳ gọi `recover_pipeline()` — chunk PROCESSING quá 10 phút hoặc worker mất heartbeat > 90s được reset về PENDING/DISCOVERED, chunk vượt `STT_MAX_ATTEMPTS` → FAILED, session `DISCOVERED` quá 30 phút không ai claim → FAILED.
