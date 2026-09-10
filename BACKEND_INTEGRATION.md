# Backend Integration Guide (SIH 26034 - Legal Metrology Compliance System)

This document serves as the official frontend integration contract for the **Legal Metrology Compliance Backend**. It describes the actual implementation, endpoints, authentication model, request/response payloads, and workflows so the frontend team can seamlessly connect without needing to inspect Python code.

---

## 1. Backend Overview

* **Technology:** Python 3.14, FastAPI, SQLAlchemy, Pydantic, PaddleOCR, OpenCV, Pandas.
* **Application Entry Point:** `backend.main:app`
* **Local Development Base URL:** `http://localhost:8000`
* **API Prefix:** `/api/v1` for versioned business routes; `/` and `/health` at root.
* **Communication:** RESTful JSON APIs over HTTP, with multipart/form-data for image uploads.
* **Role of Supabase:** Supabase provides PostgreSQL (cloud database persistence), Supabase Auth (JWT authentication), and Supabase Storage (private bucket `inspection-images` for secure image evidence).
* **Role of Backend:** Handles image intake, preprocessing, PaddleOCR, text normalization, structured field extraction with confidence/ambiguity tracking, multi-image grouping (`inspection_id`), deterministic Legal Metrology compliance evaluation (Rules 6–26), reference catalogue searching (Open Food Facts & Flipkart), and persistence.
* **Role of Frontend:** Renders UI, handles user login via Supabase Auth, captures/selects label photos, submits scans to FastAPI, displays OCR extractions, triggers compliance evaluation, and presents compliance results (`COMPLIANT`, `NON_COMPLIANT`, `REVIEW`) and auxiliary catalogue match data.

---

## 2. How to Start the Backend Locally

### Prerequisites
* Python 3.10+ installed.

### 1. Install Dependencies
```bash
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and set required environment variables:
```bash
cp .env.example .env
```
*(For local offline/firewalled development, `DATABASE_URL` defaults to SQLite `sqlite:///./legal_metrology.db`. In production, supply your Supabase PostgreSQL connection string).*

### 3. Start the Backend Locally
```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Interactive OpenAPI / Swagger Documentation
* **Swagger UI:** `http://localhost:8000/docs`
* **ReDoc:** `http://localhost:8000/redoc`

---

## 3. Environment Variables

### Backend-only Variables (Never expose to frontend)
* `DATABASE_URL`: Direct PostgreSQL connection string or SQLite path.
* `SUPABASE_SERVICE_KEY`: Service role key used for server-side storage and admin operations.
* `SUPABASE_JWT_SECRET`: Optional JWT secret for verifying tokens.

### Frontend Variables
* `VITE_API_URL` (or equivalent): Backend API base URL (`http://localhost:8000`).
* Supabase Public URL and Anon Key (for frontend Supabase Auth SDK initialization).

---

## 4. Authentication

The backend uses **Supabase JWT Bearer Token Authentication** for protected inspection and scan endpoints.

1. **Obtaining Token:** The frontend authenticates users via the Supabase Auth SDK (`supabase.auth.signInWithPassword(...)`), which returns a session containing the `access_token`.
2. **Sending Token:** Include the token in the HTTP `Authorization` header:
   ```http
   Authorization: Bearer <supabase_access_token>
   ```
3. **Protected Endpoints:** `POST /api/v1/inspections/scan` and `POST /api/v1/inspections/{inspection_id}/evaluate`.
4. **Public Endpoints:** Root (`/`), Health (`/health`), and Catalogue Search (`/api/v1/catalogue/search`) do not require authentication.
5. **Ownership & Authorization:** Inspections are tied to the authenticated user (`user_id`). Users cannot evaluate or access inspections owned by other users (returns `403 Forbidden`).

---

## 5. API Endpoint Reference

### 1. Root Service Info
* **Method & Path:** `GET /`
* **Auth:** None (Public)
* **Purpose:** Returns basic service metadata and links to documentation.
* **Response (200 OK):**
  ```json
  {
    "service": "Legal Metrology Compliance API",
    "version": "0.1.0",
    "docs": "/docs",
    "health": "/health"
  }
  ```

### 2. Health & Database Connectivity
* **Method & Path:** `GET /health`
* **Auth:** None (Public)
* **Purpose:** Checks API status, environment, version, and database connectivity.
* **Response (200 OK):**
  ```json
  {
    "status": "healthy",
    "app_name": "Legal Metrology Compliance API",
    "environment": "development",
    "version": "0.1.0",
    "timestamp": "2026-09-10T12:00:00Z",
    "database": {
      "status": "CONNECTED",
      "engine": "sqlite",
      "supabase_configured": false,
      "details": "Database connection successful"
    }
  }
  ```

### 3. Submit Product-Label Scan (Multi-Image Support)
* **Method & Path:** `POST /api/v1/inspections/scan`
* **Auth:** Required (`Authorization: Bearer <token>`)
* **Content-Type:** `multipart/form-data`
* **Parameters:**
  * `image` (File, optional): Single label image (`image/jpeg`, `image/png`, `image/webp`, `image/heic`).
  * `images` (List[File], optional): Multiple label images belonging to the same inspection.
  * `ocr_text` (Form, optional): Client-provided raw OCR text override.
  * `product_name`, `manufacturer`, `net_quantity`, `mrp` (Form, optional): Field hints.
* **Response (201 Created):**
  ```json
  {
    "success": true,
    "message": "Scan processed successfully with 2 image(s) and inspection set to REVIEW",
    "data": {
      "id": "3b7a8246-...",
      "product_id": "8f3e1b21-...",
      "image_url": "https://...",
      "status": "REVIEW",
      "created_at": "2026-09-10T12:00:00Z",
      "updated_at": "2026-09-10T12:00:00Z",
      "extracted_data": {
        "id": "5c9b1243-...",
        "inspection_id": "3b7a8246-...",
        "product_name": "Good Bakes Cookies",
        "manufacturer": "Good Bakes Ltd, Mumbai",
        "net_quantity": "Net Qty: 200 g",
        "mrp": "MRP: Rs. 50",
        "date": "07/2026",
        "consumer_care": "care@goodbakes.com",
        "extraction_confidence": 95.5,
        "created_at": "2026-09-10T12:00:00Z",
        "updated_at": "2026-09-10T12:00:00Z"
      },
      "violations": []
    },
    "timestamp": "2026-09-10T12:00:00Z"
  }
  ```

### 4. Evaluate Compliance Rules
* **Method & Path:** `POST /api/v1/inspections/{inspection_id}/evaluate`
* **Auth:** Required (`Authorization: Bearer <token>`)
* **Path Parameters:** `inspection_id` (UUID)
* **Purpose:** Runs the deterministic Legal Metrology compliance engine (Rules 6, 10, 11, 12, 13, 14, 16, 17, 24, 26) against extracted inspection data, persists findings as violations, updates inspection status, and returns the evaluation summary.
* **Response (200 OK):**
  ```json
  {
    "success": true,
    "message": "Compliance evaluation completed successfully",
    "data": {
      "inspection_id": "3b7a8246-...",
      "applicability_status": "NORMAL",
      "applicability_reason": "Package is subject to normal Legal Metrology compliance rules.",
      "overall_status": "COMPLIANT",
      "rules": [
        {
          "rule_number": "6",
          "rule_code": "LM006",
          "status": "PASS",
          "reason": "Required Rule 6 package declarations were detected.",
          "field_name": "manufacturer",
          "detected_value": "Present",
          "severity": "HIGH",
          "evidence": []
        }
      ],
      "violations": [],
      "review_items": []
    },
    "timestamp": "2026-09-10T12:00:00Z"
  }
  ```

### 5. Search Reference Catalogue
* **Method & Path:** `GET /api/v1/catalogue/search`
* **Auth:** None (Public)
* **Query Parameters:**
  * `q` (string, required): Search query (product name, brand, or category).
  * `limit` (int, optional, default: 5): Maximum results.
* **Response (200 OK):**
  ```json
  {
    "success": true,
    "message": "Found 1 reference product matches",
    "data": [
      {
        "reference_product_id": "d1a2b3c4-...",
        "source": "open_food_facts",
        "product_name": "Organic Whole Milk",
        "brand": "Amul",
        "category": "Dairy",
        "mrp": 65.0,
        "quantity": "1 L",
        "image_url": "https://...",
        "score": 0.85
      }
    ],
    "timestamp": "2026-09-10T12:00:00Z"
  }
  ```

---

## 6. Inspection Flow

```text
1. User authenticates via Supabase Auth (obtains access_token)
        ↓
2. User captures or selects label photo(s)
        ↓
3. Frontend calls POST /api/v1/inspections/scan with Authorization header and image(s)
        ↓
4. Backend stores original image(s), processes preprocessing + PaddleOCR + normalization + extraction, creates Product, Inspection, InspectionImages, and ExtractedData (status = REVIEW)
        ↓
5. Frontend optionally searches reference catalogue GET /api/v1/catalogue/search for product context
        ↓
6. Frontend calls POST /api/v1/inspections/{inspection_id}/evaluate
        ↓
7. Backend runs Phase 3 Rule Engine (Rules 6–26), persists violations, updates inspection status (COMPLIANT / NON_COMPLIANT / REVIEW)
        ↓
8. Frontend displays final rule evaluation breakdown and compliance status
```

---

## 7. Multi-Image Support

* Multiple photos of the same physical package (e.g. front panel, back panel, side panel) can be submitted together in a single inspection.
* **Endpoint:** `POST /api/v1/inspections/scan`
* **Form-data Field:** Use `images` (multiple file inputs) and/or `image` (single file input).
* **Grouping:** All uploaded images are stored in Supabase Storage and associated with the same `inspection_id` via the `inspection_images` table.
* **Evidence Combination:** The backend extracts text from each image independently and merges non-null fields. Conflicting values across images (e.g., Image 1 shows MRP ₹120 while Image 2 shows MRP ₹150) are automatically detected and marked as `AMBIGUOUS`, routing the inspection to `REVIEW` for officer verification.

---

## 8. OCR / Extraction Results & Confidence

* Each extracted field includes field-level metadata indicating confidence and status (`CONFIDENT`, `UNCERTAIN`, `MISSING`, `AMBIGUOUS`).
* Uncertain or conflicting OCR readings remain unforced (`null`), allowing the Rule Engine to correctly evaluate them as `REVIEW` rather than inventing false compliance.

---

## 9. Compliance Evaluation Statuses

* **Rule-Level Statuses:** `PASS`, `FAIL`, `REVIEW`, `NOT_APPLICABLE`
* **Overall Compliance Statuses:**
  * `COMPLIANT`: All applicable rules passed.
  * `NON_COMPLIANT`: At least one applicable rule failed (`FAIL`).
  * `REVIEW`: Evidence is ambiguous, missing, or requires physical/legal verification.
  * *(Note: Exemption `EXEMPT` under Rule 26 is evaluated separately from compliance status and does not automatically force `COMPLIANT`).*

---

## 10. Reference Product Catalogue & Unknown Products

* The `reference_products` table indexes ~28,000 cleaned items from Open Food Facts and Flipkart.
* **Auxiliary Nature:** Reference catalogue data is auxiliary reference info and is **NOT** the legal source of truth. A mismatch between reference data and the scanned package never automatically produces `NON_COMPLIANT`.
* **Unknown Products:** Products absent from the reference catalogue can still be fully scanned, extracted, and evaluated. Catalogue matching is entirely optional.
* **Forged First Scan Safety:** Historical scans and reference data are never used as a compliance baseline. Each scan is evaluated independently against the current physical package evidence.

---

## 11. Error Handling & Status Codes

* `400 Bad Request`: Missing image or invalid file type.
* `401 Unauthorized`: Missing or invalid Bearer token.
* `403 Forbidden`: User attempting to access/evaluate another user's inspection.
* `404 Not Found`: Inspection or resource not found.
* `422 Unprocessable Entity`: Validation error in request body or parameters.
* `500 Internal Error`: Storage upload failure or database transaction error.

---

## 12. CORS Configuration

* Configured in `backend/main.py` with `allow_origins=["*"]` (open for prototype inspection clients and frontend integration).

---

## 13. Sample Frontend Integration (JavaScript/TypeScript Fetch)

### Authenticated Scan Intake (Multi-Image)
```typescript
const formData = new FormData();
formData.append("images", fileFront);
formData.append("images", fileBack);
formData.append("product_name", "Organic Milk");

const response = await fetch("http://localhost:8000/api/v1/inspections/scan", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${supabaseAccessToken}`
  },
  body: formData
});

const result = await response.json();
const inspectionId = result.data.id;
```

### Compliance Evaluation
```typescript
const evalResponse = await fetch(`http://localhost:8000/api/v1/inspections/${inspectionId}/evaluate`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${supabaseAccessToken}`
  }
});

const evaluation = await evalResponse.json();
console.log("Overall Status:", evaluation.data.overall_status);
```

### Catalogue Search
```typescript
const searchResponse = await fetch("http://localhost:8000/api/v1/catalogue/search?q=Amul&limit=3");
const catalogueMatches = await searchResponse.json();
```

---

## 14. Frontend Integration Checklist

- [ ] Configure frontend API base URL (`http://localhost:8000`)
- [ ] Initialize Supabase Auth in frontend
- [ ] Implement login / session management
- [ ] Pass `Authorization: Bearer <token>` on `/scan` and `/evaluate` requests
- [ ] Allow uploading multiple images for a single inspection scan
- [ ] Display extracted fields, confidence, and status (`CONFIDENT`/`AMBIGUOUS`)
- [ ] Trigger compliance evaluation endpoint
- [ ] Render rule-level results (`PASS`/`FAIL`/`REVIEW`) and overall status (`COMPLIANT`/`NON_COMPLIANT`/`REVIEW`)
- [ ] Handle catalogue search results optionally

---

## Frontend Quick Start

1. Start backend: `python -m uvicorn backend.main:app --reload`
2. Sign in via Supabase Auth on frontend to obtain access token.
3. Submit label photo(s) to `POST /api/v1/inspections/scan`.
4. Trigger compliance evaluation at `POST /api/v1/inspections/{inspection_id}/evaluate`.
5. Display results.
