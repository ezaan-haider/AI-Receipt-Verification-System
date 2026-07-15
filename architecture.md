## Architecture

```mermaid
flowchart TD

    E[Employee]
    A[Administrator]

    FE[Streamlit Frontend]

    API[FastAPI Backend]

    CV[Google Gemini Vision]

    DB[(Supabase PostgreSQL)]

    CL[(Cloudinary)]

    V[Verification Engine]

    E --> FE
    A --> FE

    FE --> API

    API --> CL
    API --> DB

    API --> CV

    CV --> API

    API --> V

    V --> DB

    API --> FE
```
