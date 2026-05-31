# SAGE — API Contract

The shared agreement on backend endpoints. Tanjid defines these;
Abrar and Minhazul build against them. This lets the frontend be
built with fake data before the real backend is finished.

## Endpoints (planned)

POST /auth/signup     -> { email, password, name } => { token }
POST /auth/login      -> { email, password }        => { token }
POST /chat            -> { message, session_id }     => { reply, tools_used }
POST /documents/upload-> file (multipart)            => { document_id, status }
GET  /documents       -> (auth)                      => [ documents ]

(To be finalized in Step 3.)
