
import json
import sys
import urllib.request
import urllib.error

BASE='http://localhost:5001/api'

def http(method, path, data=None, token=None):
    url = BASE + path
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    if data is not None:
        body = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    else:
        body = None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode('utf-8', errors='replace')
            try:
                js = json.loads(raw)
            except Exception:
                js = raw
            return resp.status, js
    except urllib.error.HTTPError as e:
        raw = e.read().decode('utf-8', errors='replace')
        try:
            js = json.loads(raw)
        except Exception:
            js = raw
        return e.code, js

def check(name, got, expected):
    ok = (got == expected)
    print(('PASS' if ok else 'FAIL') + f' - {name}: got {got}, expected {expected}')
    return ok

def login(username, password):
    st, js = http('POST', '/login', {'username': username, 'password': password})
    if st != 200:
        print('FAIL - login', username, st, js)
        return None
    token = None
    if isinstance(js, dict):
        token = js.get('token') or (js.get('data') or {}).get('token')
    if not token:
        print('FAIL - login no token', username, js)
        return None
    print('PASS - login', username)
    return token

admin_token = login('admin','admin123')
user_token = login('admin1','admin123')
if not admin_token or not user_token:
    sys.exit(1)

print('\n=== 普通用户(admin1)回归 ===')
check('GET /stats (should 403)', http('GET','/stats', token=user_token)[0], 403)
check('GET /stats/me (should 200)', http('GET','/stats/me', token=user_token)[0], 200)
check('GET /users (should 403)', http('GET','/users', token=user_token)[0], 403)
check('GET /uploads (should 200)', http('GET','/uploads?page=1&page_size=5', token=user_token)[0], 200)

print('\n=== 管理员(admin)回归 ===')
check('GET /stats (should 200)', http('GET','/stats', token=admin_token)[0], 200)
check('GET /users (should 200)', http('GET','/users', token=admin_token)[0], 200)
check('GET /identification/tasks (should 200)', http('GET','/identification/tasks?page=1&page_size=5', token=admin_token)[0], 200)
check('GET /identification/tasks?user_id=1 (should 200)', http('GET','/identification/tasks?page=1&page_size=5&user_id=1', token=admin_token)[0], 200)

print('\n=== 回归结束 ===')
