# AI Receipt Verification System

An end-to-end AI-powered receipt verification platform capable of extracting structured information from both digital and handwritten receipts using Google's Gemini Vision model.

The project was originally commissioned with a simple objective:

> **Extract receipt information (particularly the receipt amount) from both digital and handwritten receipts.**

Instead of building only an extraction script, this project evolved into a complete cloud-based receipt verification system that automates receipt processing, performs verification, detects duplicates, supports manual review, and provides role-based access for employees and administrators.

---

# Demo

https://ai-receipt-verification-system.streamlit.app

---

# Table of Contents

- Overview
- Problem Statement
- Solution
- Features
- System Workflow
- Architecture
- Technology Stack
- Folder Structure
- Backend
- Frontend
- Database Design
- Verification Logic
- Authentication
- Deployment
- Running Locally
- API Endpoints
- Future Improvements
- Author

---

# Overview

Organizations often receive hundreds or thousands of employee expense claims every month.

Manual verification is time-consuming and prone to human error.

Employees submit

- photographs
- scanned receipts
- handwritten receipts

which then need to be validated before reimbursement.

The objective of this project is to automate as much of this process as possible while still allowing manual review whenever the AI is uncertain.

---

# Original Requirement

The software house required a system capable of:

- extracting information from digital receipts
- extracting information from handwritten receipts
- identifying the receipt amount

No restrictions were placed on the underlying technology.

Initially, the project began using a traditional OCR pipeline.

After experimentation, the architecture was redesigned to use a Vision Language Model (Google Gemini Vision), which produced significantly better extraction quality and drastically reduced processing time.

---

# Final Solution

The final solution is a cloud-based AI receipt verification platform consisting of

- Employee Portal
- Administrator Dashboard
- AI Receipt Extraction
- Automated Verification Engine
- Manual Review Workflow
- Cloud Image Storage
- Hosted PostgreSQL Database

---

# Features

## Employee

- Secure login
- Upload receipt
- Enter claim amount
- View submitted receipts
- Track verification status

---

## Administrator

- Secure login
- View every submitted receipt
- Process receipts using AI
- Review extracted information
- Approve receipts
- Reject receipts
- Permanently delete receipts

---

## AI Extraction

Google Gemini Vision extracts:

- Complete receipt transcription
- Vendor name
- Receipt date
- Receipt total
- Currency
- Receipt number
- Confidence score
- Extraction warnings

The full receipt text is preserved to allow auditing and future processing.

---

## Verification

The backend validates:

- Claim amount vs receipt total
- Receipt date validity
- Future dates
- Exact duplicate images
- Possible duplicate receipts
- Missing fields
- Low confidence extraction

---

# System Workflow

```
Employee Login
        │
        ▼
Upload Receipt + Claim Amount
        │
        ▼
Receipt stored in Cloudinary
        │
        ▼
Metadata stored in Supabase
        │
        ▼
Administrator processes receipt
        │
        ▼
Gemini Vision Analysis
        │
        ▼
Structured Information Extraction
        │
        ▼
Backend Verification
        │
        ▼
Administrator Review
        │
        ▼
Approve / Reject / Delete
```

---

# System Architecture

```text
                           +-----------------------+
                           |     Employee Portal   |
                           +----------+------------+
                                      |
                                      |
                           Upload Receipt + Claim
                                      |
                                      v
                        +----------------------------+
                        |      FastAPI Backend       |
                        +----------------------------+
                                      |
             +------------------------+-------------------------+
             |                        |                         |
             |                        |                         |
             v                        v                         v
     +----------------+     +---------------------+     +------------------+
     |   Cloudinary   |     |   Gemini Vision    |     |    Supabase      |
     | Image Storage  |     | AI Extraction      |     | PostgreSQL DB    |
     +----------------+     +---------------------+     +------------------+
                                      |
                                      v
                          Verification Engine
                                      |
                                      v
                          Administrator Dashboard
```

---

# Technology Stack

## Backend

- FastAPI
- SQLAlchemy
- JWT Authentication
- Pydantic
- Python

---

## AI

- Google Gemini Vision

---

## Database

- Supabase PostgreSQL

---

## Image Storage

- Cloudinary

---

## Frontend

- Streamlit

---

## Deployment

- Render
- Streamlit Community Cloud

---

## Containerization

- Docker
- Docker Compose

---

# Project Structure

```
backend/
    app/
        services/
        models.py
        schemas.py
        auth.py
        dependencies.py
        database.py
        main.py

frontend/
    app.py
    api_client.py

docker-compose.yaml
README.md
```

---

# Verification Logic

The backend performs deterministic verification after AI extraction.

Rules include:

- Claim amount matches receipt total
- Date exists
- Date is valid
- Date is not in the future
- Exact duplicate detection
- Possible duplicate detection
- Missing required information

The AI performs extraction only.

Business rules remain entirely deterministic inside the backend.

---

# Authentication

JWT-based authentication.

Two roles exist:

## Employee

Can

- upload receipts
- view personal receipts

Cannot

- review
- delete
- access administrator dashboard

---

## Administrator

Can

- process receipts
- review receipts
- approve
- reject
- delete

---

# Deployment

Frontend

- Streamlit Community Cloud

Backend

- Render

Database

- Supabase

Image Storage

- Cloudinary

---

# API

## Authentication

POST

```
/auth/login
```

---

## Employee

POST

```
/receipts
```

GET

```
/receipts/me
```

---

## Administrator

POST

```
/receipts/{id}/process
```

PATCH

```
/receipts/{id}/review
```

DELETE

```
/receipts/{id}
```

GET

```
/receipts
```

GET

```
/receipts/{id}
```

---

# Running Locally

```bash
git clone <repository>

cd AI-Receipt-Verification-System

docker compose up --build
```

Frontend

```
localhost:8501
```

Backend

```
localhost:8000/docs
```

---

# Future Improvements

Potential future enhancements include:

- Google OAuth authentication
- Automatic receipt processing after upload
- Analytics dashboard
- Receipt fraud detection
- OCR fallback model
- Multi-language receipt support
- Receipt categorization
- Line-item extraction
- PDF receipt support
- Email notifications
- Audit logging
- CI/CD pipeline using GitHub Actions
- Unit and integration testing

---

# Author

Developed by

**Ezaan Haider**

AI Engineer | Data Scientist

This project demonstrates the design and implementation of a complete AI-powered receipt verification platform using modern cloud infrastructure, vision-language models, REST APIs, containerization, and secure authentication.
