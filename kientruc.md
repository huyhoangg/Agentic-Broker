Chuẩn. Nếu **bỏ queue**, tôi còn thích kiến trúc MVP này hơn vì pipeline của anh đang khá tuyến tính và chưa cần scale phức tạp.

Tôi sẽ chuyển thành **DB-driven pipeline + worker polling**, trong đó **Supabase Postgres chính là state machine**.

```text
                    ┌─────────────────────────┐
                    │      ADMIN CONSOLE      │
                    │        Next.js          │
                    └───────────┬─────────────┘
                                │
                         Supabase / API
                                │
                    ┌───────────▼─────────────┐
                    │          API            │
                    │        FastAPI          │
                    └───────────┬─────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
       ┌────────────┐    ┌────────────┐    ┌────────────┐
       │  Scanner   │    │  Capture   │    │     STT    │
       │            │    │            │    │            │
       │ detect     │───▶│ ffmpeg     │───▶│ Whisper    │
       │ live       │    │ save audio │    │            │
       └────────────┘    └────────────┘    └─────┬──────┘
                                                 │
                                                 ▼
                                          ┌────────────┐
                                          │ Transcript │
                                          │  Supabase  │
                                          └─────┬──────┘
                                                │
                                                ▼
                                             Groq
```

## 1. Không queue → Database điều phối

Thay vì:

```text
capture → queue → STT
```

ta dùng:

```text
capture
   ↓
Supabase
   ↓
STT worker tự poll
```

Ví dụ `audio_chunks`:

```text
id
live_session_id
sequence

storage_path

status
created_at
transcribed_at
error
```

Status:

```text
PENDING
   ↓
PROCESSING
   ↓
COMPLETED
```

hoặc:

```text
PENDING → FAILED
```

STT worker cứ mỗi vài giây query:

```sql
SELECT *
FROM audio_chunks
WHERE status = 'PENDING'
ORDER BY created_at
LIMIT 1;
```

Lấy được chunk → đổi:

```text
PENDING → PROCESSING
```

→ Whisper → save transcript → `COMPLETED`.

---

# 2. Capture cũng dùng state tương tự

`live_sessions`:

```text
DISCOVERED
    ↓
CAPTURING
    ↓
ENDED
    ↓
FINALIZING
    ↓
COMPLETED
```

Scanner chỉ có nhiệm vụ:

```text
scan source
   ↓
live?
   ↓
upsert live_session
```

Capture worker nhìn:

```sql
status = 'DISCOVERED'
```

rồi bắt đầu capture.

---

# 3. Tôi sẽ không để API làm việc nặng

Cấu trúc process:

```text
Render
│
├── api
│    └── FastAPI
│
├── console
│    └── Next.js
│
├── scanner
│    └── Python
│
├── capture
│    └── Python + FFmpeg
│
└── stt
     └── Python + Whisper
```

Mỗi cái là **long-running service riêng**.

Không cần queue.

---

# 4. Điểm quan trọng: worker claim job bằng Postgres

Không nên để:

```text
worker A đọc PENDING
worker B đọc PENDING
```

cùng lúc.

Dùng transaction/row locking:

```sql
SELECT *
FROM audio_chunks
WHERE status = 'PENDING'
ORDER BY created_at
FOR UPDATE SKIP LOCKED
LIMIT 1;
```

sau đó:

```text
PENDING
   ↓
PROCESSING
worker_id = xxx
started_at = ...
```

Như vậy sau này anh chạy:

```text
1 STT worker
```

hoặc:

```text
5 STT workers
```

vẫn được mà **không cần queue**.

---

# 5. Supabase trở thành control plane

Đây là architecture tôi thấy rất hợp với case của anh:

```text
                SUPABASE
        ┌──────────────────────┐
        │                      │
        │ PostgreSQL           │
        │ ├── sources          │
        │ ├── live_sessions    │
        │ ├── audio_chunks     │
        │ ├── transcripts      │
        │ ├── jobs/state       │
        │ └── logs             │
        │                      │
        │ Storage              │
        │ └── audio            │
        │                      │
        │ Realtime             │
        └──────────┬───────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
     Scanner    Capture       STT
```

Console subscribe Supabase Realtime nên khi:

```text
audio chunk created
```

UI tự cập nhật.

Không cần websocket server riêng.

---

# 6. Nhưng vẫn nên có `jobs`

"Bỏ queue" **không có nghĩa là bỏ job tracking**.

Tôi vẫn tạo:

```text
jobs
```

nhưng nó chỉ là **audit/state table**, không phải message queue.

```text
jobs
----
id
type
entity_type
entity_id

status

worker
attempt
started_at
finished_at

error
metadata
```

Ví dụ:

```text
capture / live_session_123 / RUNNING

transcribe / audio_chunk_456 / COMPLETED

transcribe / audio_chunk_457 / FAILED
```

Console nhìn vào bảng này để biết hệ thống đang làm gì.

---

# 7. Console lúc này sẽ rất đẹp

Dashboard:

```text
┌──────────────────────────────────────────────────────┐
│ LIVE PIPELINE                                        │
├──────────────────────────────────────────────────────┤
│                                                      │
│ Sources             12                               │
│ Live                 3                               │
│ Capturing            3                               │
│ Audio pending        2                               │
│ STT processing       1                               │
│ Failed               0                               │
│                                                      │
├──────────────────────────────────────────────────────┤
│ ACTIVE LIVES                                         │
│                                                      │
│ 🔴 Broker A                                          │
│    Capture ████████████████                         │
│    STT     ██████████████░░                         │
│    37 chunks                                         │
│                                                      │
│ 🔴 Broker B                                          │
│    Capture ████████████████                         │
│    STT     ████████████████                         │
│    21 chunks                                         │
└──────────────────────────────────────────────────────┘
```

Click vào live:

```text
Live
├── Overview
├── Audio
├── Transcript
├── Processing
└── Logs
```

---

# 8. Tôi sẽ thêm một thứ: Heartbeat

Vì không có queue manager, worker chết phải phát hiện được.

Mỗi worker có:

```text
workers
-------
id
type
hostname
status
last_heartbeat
current_task
```

Ví dụ:

```text
scanner
● healthy
last heartbeat: 2 sec ago

capture-01
● healthy
capturing live_123

stt-01
● healthy
transcribing chunk_938
```

Nếu:

```text
last_heartbeat > 60 sec
```

console:

```text
⚠ STT worker offline
```

---

# 9. Recovery cũng dựa vào DB

Ví dụ STT worker chết giữa chừng:

```text
audio_chunk
status = PROCESSING
started_at = 10:31
```

worker chết.

Một watchdog phát hiện:

```text
PROCESSING > 10 minutes
```

→ reset:

```text
PROCESSING → PENDING
```

rồi worker khác lấy lại.

Không cần queue.

---

# 10. Core architecture tôi chốt cho MVP

```text
                    ┌─────────────────┐
                    │    Next.js      │
                    │ Admin Console   │
                    └────────┬────────┘
                             │
                       Supabase/API
                             │
        ┌────────────────────┴─────────────────────┐
        │                  Supabase                 │
        │                                           │
        │ PostgreSQL       Storage       Realtime   │
        └───┬──────────────┬─────────────────┬─────┘
            │              │                 │
       ┌────▼────┐    ┌────▼─────┐     ┌────▼────┐
       │ Scanner │    │ Capture  │     │   STT   │
       │ Worker  │    │ Worker   │     │ Worker  │
       └─────────┘    └──────────┘     └─────────┘
            │              │                 │
            │              │                 │
            ▼              ▼                 ▼
         Sources        FFmpeg             Whisper
                            │
                            ▼
                         Audio
                            │
                            ▼
                       Transcript
                            │
                            ▼
                           Groq
```

### Stack MVP

**Next.js + FastAPI + Supabase + Python Workers + FFmpeg + Whisper + Groq + Render.**

Không Redis.
Không Kafka.
Không Celery.
Không message broker.

Đến khi volume tăng thật sự mới thêm queue.

**Một điểm tôi sẽ giữ ngay từ đầu:** toàn bộ pipeline phải thiết kế theo kiểu **idempotent + state machine + worker heartbeat + retry/recovery**. Như vậy dù hiện tại chỉ có 3–10 broker, sau này scale lên hàng trăm source vẫn không phải đập kiến trúc đi làm lại.
