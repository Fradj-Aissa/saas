# 🤖 Master Prompt — بناء محرك PDF AI Backend

> انسخ هذا الـ Prompt كاملاً وأعطه للذكاء الاصطناعي

---

## الـ Prompt

```
أنت مهندس Backend خبير متخصص في Python و FastAPI وأنظمة AI.
مهمتك بناء محرك PDF ذكي احترافي بالكامل خطوة بخطوة.

══════════════════════════════════════════
                نظرة عامة
══════════════════════════════════════════

المشروع: محرك PDF AI Engine
الـ Stack: Python + FastAPI + Celery + Redis + PostgreSQL
الهدف: استقبال ملفات PDF، تحليلها، استخراج محتواها، وتحويله إلى Markdown منظم مع دعم تصدير PDF و DOCX

يوجد Frontend جاهز بـ React — مهمتك Backend فقط.

══════════════════════════════════════════
              قواعد العمل الإلزامية
══════════════════════════════════════════

1. نفّذ كل شيء خطوة بخطوة بالترتيب الذي سأحدده
2. اكتب الكود الكامل القابل للتشغيل فوراً — لا placeholders، لا "..." ناقصة
3. لكل ملف اكتب المسار الكامل قبل الكود
4. بعد كل مرحلة أخبرني بما تم وما التالي
5. إذا واجهت تعارضاً بين مكتبتين اشرح واختر الأفضل
6. اكتب تعليقات بالعربية داخل الكود لكل section مهم
7. لا تستخدم sync حيث يجب async
8. لا تكتب كود demo — اكتب كود production-ready

══════════════════════════════════════════
            هيكل المشروع المطلوب
══════════════════════════════════════════

backend/
├── app/
│   ├── api/v1/
│   │   ├── auth.py
│   │   ├── documents.py
│   │   ├── exports.py
│   │   └── websocket.py
│   ├── core/
│   │   ├── config.py          ← pydantic-settings
│   │   ├── security.py        ← JWT
│   │   ├── exceptions.py
│   │   ├── logging.py
│   │   └── rate_limiter.py
│   ├── db/
│   │   ├── base.py
│   │   ├── session.py
│   │   └── migrations/        ← Alembic
│   ├── models/
│   │   ├── user.py
│   │   ├── document.py
│   │   └── output.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── document.py
│   │   └── output.py
│   ├── services/
│   │   ├── document_service.py
│   │   ├── storage_service.py  ← Local/S3 Abstraction
│   │   ├── export_service.py
│   │   └── file_validator.py
│   ├── workers/
│   │   ├── celery_app.py
│   │   ├── celery_beat.py
│   │   ├── pdf_processor.py
│   │   └── tasks/
│   │       ├── detect_type.py
│   │       ├── extract_text.py
│   │       ├── extract_tables.py
│   │       ├── extract_images.py
│   │       └── build_markdown.py
│   ├── ai/
│   │   ├── ocr/
│   │   │   ├── easyocr_engine.py
│   │   │   ├── paddle_engine.py
│   │   │   ├── tesseract_engine.py
│   │   │   └── ocr_manager.py
│   │   ├── vision/
│   │   │   └── google_vision.py
│   │   ├── gemini/
│   │   │   ├── gemini_client.py
│   │   │   ├── text_chunker.py
│   │   │   └── prompts.py
│   │   └── image_processor.py
│   ├── utils/
│   │   ├── pdf_detector.py
│   │   ├── arabic_utils.py
│   │   └── file_utils.py
│   └── main.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── .env.example
├── requirements.txt
├── alembic.ini
├── Makefile
└── docker-compose.yml

══════════════════════════════════════════
         ترتيب التنفيذ — اتبعه حرفياً
══════════════════════════════════════════

─────────────────────────────────────────
المرحلة 1: البنية التحتية
─────────────────────────────────────────
ابدأ بهذه الملفات بالترتيب:

1. requirements.txt — بجميع الحزم المطلوبة
2. .env.example — بجميع المتغيرات
3. app/core/config.py — pydantic-settings يقرأ .env
4. app/core/logging.py — structlog مع JSON format
5. app/core/exceptions.py — Custom HTTP Exceptions
6. app/db/base.py — SQLAlchemy Base
7. app/db/session.py — AsyncSession + get_db dependency
8. alembic.ini + app/db/migrations/env.py
9. docker-compose.yml — FastAPI + PostgreSQL + Redis + Celery + Flower
   ● يجب أن يحتوي على healthcheck لكل service
   ● depends_on بشرط service_healthy
10. app/main.py — FastAPI app مع CORS + Routers + /health endpoint

─────────────────────────────────────────
المرحلة 2: Auth + Upload
─────────────────────────────────────────
11. app/models/user.py — UUID primary key, email, hashed_password
12. app/models/document.py — مع هذه الحالات فقط:
    uploaded → queued → processing → ocr → formatting → completed → failed
13. app/models/output.py — markdown_path, pdf_path, docx_path
14. app/schemas/auth.py — RegisterRequest, LoginRequest, TokenResponse
15. app/schemas/document.py — UploadResponse, DocumentStatus, DocumentDetail
16. app/core/security.py — hash_password, verify_password, create_jwt, decode_jwt
17. app/api/v1/auth.py — POST /register, POST /login, GET /me
18. app/services/file_validator.py:
    ● فحص MIME الحقيقي بـ python-magic وليس الاسم فقط
    ● حد الحجم من Settings
    ● منع Path Traversal
    ● إعادة safe_filename
19. app/services/storage_service.py:
    ● Abstract class BaseStorage مع: save, get, delete, get_url
    ● LocalStorage implementation
    ● S3Storage stub للمستقبل
    ● get_storage() factory function
20. app/api/v1/documents.py:
    ● POST /upload — يستقبل PDF، يتحقق، يحفظ، يُنشئ document في DB، يرسل لـ Celery
    ● GET /{id}/status — حالة المستند + نسبة التقدم
    ● GET /{id}/result — نتيجة المعالجة
    ● DELETE /{id} — حذف المستند وملفاته
    ● GET / — قائمة مستندات المستخدم

─────────────────────────────────────────
المرحلة 3: PDF Detection
─────────────────────────────────────────
21. app/utils/pdf_detector.py:
    ● استخدم PyMuPDF (fitz)
    ● احسب نسبة الصفحات النصية مقابل الصور
    ● إذا text_ratio > 0.8 → "text"
    ● إذا image_ratio > 0.8 → "scanned"
    ● إذا كلاهما > 0.3 → "mixed"
    ● غير ذلك → "handwritten" يُحدَّد بعد OCR
    ● أعد: { type, text_ratio, image_ratio, total_pages }

─────────────────────────────────────────
المرحلة 4: OCR System
─────────────────────────────────────────
22. app/ai/image_processor.py — OpenCV pipeline:
    ● grayscale → denoise → deskew → CLAHE → adaptive threshold
    ● دالة منفصلة لكل خطوة
    ● دالة preprocess_for_ocr() تجمعهم

23. app/ai/ocr/easyocr_engine.py:
    ● تهيئة lazy (لا تحمّل النموذج إلا عند الحاجة)
    ● languages = ['ar', 'en']
    ● أعد: OCRResult(text, confidence, engine="easyocr")

24. app/ai/ocr/paddle_engine.py:
    ● نفس الـ interface
    ● lang='arabic'
    ● أعد: OCRResult(text, confidence, engine="paddleocr")

25. app/ai/ocr/tesseract_engine.py:
    ● lang='ara+eng'
    ● احسب confidence من output dataframe
    ● أعد: OCRResult(text, confidence, engine="tesseract")

26. app/ai/vision/google_vision.py:
    ● GoogleVisionEngine class
    ● extract_text(image_bytes) → يستخدم DOCUMENT_TEXT_DETECTION
    ● extract_handwritten(image_bytes)
    ● extract_table_from_image(image_bytes) → يعيد list of rows
    ● _calculate_confidence() من word confidences
    ● VisionCostController class:
      - MAX_CALLS_PER_DOCUMENT من Settings (default: 10)
      - MAX_CALLS_PER_DAY من Settings (default: 1000)
      - can_call(document_id) → (bool, reason)
      - record_call(document_id)
      - get_stats() → daily usage

27. app/ai/ocr/ocr_manager.py:
    ● CONFIDENCE_THRESHOLD = 0.7
    ● يجرب المحركات بالترتيب: EasyOCR → PaddleOCR → Tesseract → Google Vision
    ● قبل Google Vision: يفحص VisionCostController.can_call()
    ● إذا رُفض Google Vision: يعيد أفضل نتيجة متاحة مع warning
    ● يسجل في الـ log أي محرك استُخدم وما الـ confidence

─────────────────────────────────────────
المرحلة 5: Gemini + Markdown
─────────────────────────────────────────
28. app/ai/gemini/text_chunker.py:
    ● MAX_TOKENS_PER_CHUNK = 3000
    ● chunk_text(text) → list[str]
    ● يقسّم على أساس الفقرات (\n\n)
    ● لا يقطع في منتصف جملة

29. app/ai/gemini/prompts.py:
    ● ARABIC_MARKDOWN_PROMPT — لتحويل OCR إلى Markdown مع تصحيح أخطاء
    ● TABLE_EXTRACTION_PROMPT — لاستخراج جداول من نص
    ● HANDWRITTEN_CLEANUP_PROMPT — لتنظيف الكتابة اليدوية
    ● كل prompt يتضمن قواعد: الحفاظ على النص، RTL، لا حذف، Markdown فقط

30. app/ai/gemini/gemini_client.py:
    ● GeminiClient class
    ● format_text(text) → يقسّم بـ text_chunker ثم يرسل chunk بـ chunk
    ● يجمع النتائج بالترتيب
    ● retry logic: 3 محاولات مع exponential backoff
    ● يسجل token usage لكل طلب

─────────────────────────────────────────
المرحلة 6: Extraction Tasks
─────────────────────────────────────────
31. app/workers/tasks/extract_text.py:
    ● إذا text PDF: استخدم PyMuPDF مباشرة
    ● إذا scanned/mixed: حوّل الصفحة لصورة → preprocess → OCRManager
    ● أعد قاموس { page_number: text } لكل صفحة

32. app/workers/tasks/extract_tables.py:
    ● إذا text PDF: Camelot بـ flavor='lattice' أولاً ثم 'stream'
    ● إذا scanned: img2table
    ● إذا handwritten: Google Vision extract_table_from_image
    ● حوّل كل جدول إلى Markdown Table
    ● أعد list[str] من Markdown Tables

33. app/workers/tasks/extract_images.py:
    ● PyMuPDF لاستخراج الصور
    ● احفظ كل صورة في outputs/{user_id}/images/
    ● أعد list[str] من المسارات النسبية

34. app/workers/tasks/build_markdown.py:
    ● يجمع النصوص + الجداول + الصور في Markdown واحد منظم
    ● الصور تُضاف كـ ![image_N](path)
    ● الجداول تُوضع في مكانها الصحيح حسب رقم الصفحة
    ● يمرر النتيجة لـ GeminiClient.format_text()
    ● يحفظ الـ Markdown النهائي

─────────────────────────────────────────
المرحلة 7: Celery Pipeline
─────────────────────────────────────────
35. app/workers/celery_app.py:
    ● broker + backend = Redis URL
    ● task_acks_late = True
    ● task_reject_on_worker_lost = True
    ● Queues: pdf_processing, ocr, ai_formatting
    ● max_retries = 3، default_retry_delay = 60
    ● beat_schedule: cleanup_old_files كل 24 ساعة

36. app/workers/celery_beat.py:
    ● cleanup_old_files(): يحذف الملفات الأقدم من 7 أيام
    ● يحدّث حالة المستندات المنتهية الصلاحية في DB

37. app/workers/pdf_processor.py — Main Task:
    ● @celery_app.task(bind=True, max_retries=3)
    ● خطوات بالترتيب مع تحديث الحالة والـ progress بعد كل خطوة:
      1. uploaded (0%)  → detect type
      2. queued (10%)   → save type to DB
      3. processing (20%) → extract text
      4. ocr (40%)     → run OCR if needed
      5. ocr (60%)     → extract tables + images
      6. formatting (80%) → Gemini format
      7. formatting (90%) → build final markdown
      8. completed (100%) → save output to DB
    ● عند الفشل: update status = failed، حفظ error_message، Sentry capture
    ● عند MaxRetriesExceeded: status = failed نهائياً

─────────────────────────────────────────
المرحلة 8: WebSocket
─────────────────────────────────────────
38. app/api/v1/websocket.py:
    ● ConnectionManager class: connect, disconnect, send_progress
    ● @router.websocket("/progress/{document_id}")
    ● يقرأ الحالة من DB كل ثانيتين
    ● يرسل JSON: { status, progress, message, current_page, total_pages }
    ● ينهي الاتصال تلقائياً عند completed أو failed

─────────────────────────────────────────
المرحلة 9: Export System
─────────────────────────────────────────
39. app/services/export_service.py:
    ● export_to_pdf(markdown_path, output_path):
      pandoc مع xelatex + Amiri font + RTL + margin=2cm
    ● export_to_docx(markdown_path, output_path):
      pandoc مع reference-doc للـ RTL
    ● كلاهما async بـ asyncio.create_subprocess_exec
    ● يرفع exception واضح عند فشل pandoc

40. app/api/v1/exports.py:
    ● POST /{document_id}/pdf
    ● POST /{document_id}/docx
    ● GET /{document_id}/download/{format}
    ● يتحقق أن status = completed قبل التصدير

─────────────────────────────────────────
المرحلة 10: Tests + Finalize
─────────────────────────────────────────
41. tests/conftest.py:
    ● pytest fixtures: async_client, db_session, auth_token, sample_pdf

42. tests/unit/:
    ● test_pdf_detector.py
    ● test_ocr_manager.py — mock المحركات الخارجية
    ● test_text_chunker.py
    ● test_file_validator.py
    ● test_google_vision.py — mock Vision API
    ● test_cost_controller.py

43. tests/integration/:
    ● test_auth_api.py — register + login + me
    ● test_upload_api.py — upload PDF + check status
    ● test_processing_pipeline.py — pipeline كامل بـ mock OCR

44. Makefile:
    dev, worker, beat, migrate, migration, test, docker-up, docker-down

══════════════════════════════════════════
         المتطلبات التقنية الإلزامية
══════════════════════════════════════════

Python: 3.11+

الحزم الإلزامية في requirements.txt:
  fastapi>=0.111.0
  uvicorn[standard]
  python-multipart
  pydantic-settings>=2.0
  sqlalchemy[asyncio]>=2.0
  asyncpg
  alembic
  celery[redis]>=5.3
  redis>=5.0
  python-jose[cryptography]
  passlib[bcrypt]
  slowapi
  structlog
  sentry-sdk[fastapi]
  pymupdf
  easyocr
  paddleocr
  paddlepaddle
  pytesseract
  google-cloud-vision
  google-generativeai
  opencv-python-headless
  camelot-py[cv]
  img2table
  python-magic
  pytest
  pytest-asyncio
  httpx
  pytest-cov

══════════════════════════════════════════
              متطلبات الجودة
══════════════════════════════════════════

● كل دالة async لها نظيرة sync إذا لزم
● كل استدعاء خارجي (OCR / API) محاط بـ try/except مع logging واضح
● كل endpoint محمي بـ JWT ما عدا /health و /register و /login
● لا يُرسل أي error داخلي للـ client — استخدم رسائل عامة
● كل file path يُبنى بـ pathlib.Path وليس string concatenation
● كل model له __repr__ مفيد للـ debugging
● لا hard-coded secrets — كل شيء من Settings

══════════════════════════════════════════
         نقاط خاصة بدعم اللغة العربية
══════════════════════════════════════════

● OCR Manager: language hints = ['ar', 'en'] دائماً
● Gemini Prompts: تتضمن تعليمات RTL وتصحيح الهمزات والحروف المتشابهة
● Export PDF: pandoc مع -V lang=ar -V dir=rtl -V mainfont="Amiri"
● Export DOCX: reference-doc يدعم RTL
● arabic_utils.py: دوال لـ is_arabic_text(), fix_arabic_punctuation(), ensure_rtl_marks()

══════════════════════════════════════════
                 ابدأ الآن
══════════════════════════════════════════

ابدأ بالمرحلة 1 فوراً.
اكتب كل ملف بكوده الكامل.
بعد إنهاء كل مرحلة قل:
  "✅ المرحلة [X] مكتملة — الملفات المكتوبة: [قائمة] — التالي: المرحلة [X+1]"
ثم انتظر موافقتي قبل الانتقال للمرحلة التالية.
```

---

## تعليمات الاستخدام

### 1. للـ Claude / ChatGPT / Gemini
انسخ الـ Prompt الموجود في الكود البرمجي أعلاه وأرسله مباشرة.

### 2. للحصول على أفضل نتيجة

| النموذج | الطريقة المثلى |
|---------|---------------|
| Claude Sonnet | أرسل الـ Prompt كاملاً دفعة واحدة |
| GPT-4o | أرسله مع System Prompt: "أنت مهندس Python خبير" |
| Gemini 1.5 Pro | أضف في البداية: "فكّر خطوة بخطوة قبل الكتابة" |

### 3. نصائح للمتابعة

بعد كل مرحلة يجيب الـ AI، قل له:
```
✅ ممتاز، انتقل للمرحلة التالية
```
أو إذا أردت تعديلاً:
```
في المرحلة [X]، الملف [Y]، عدّل [التعديل المطلوب] ثم انتقل للتالية
```

### 4. إذا توقف الـ AI في المنتصف
قل له:
```
واصل من حيث توقفت — آخر ملف كتبته كان [اسم الملف]
```

---

*النسخة 1.0 — Prompt مبني على خطة PDF AI Engine v2.1*
