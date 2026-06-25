
#!/usr/bin/env python3
import hashlib
import json
import secrets
import sys
from pathlib import Path
from datetime import datetime

import uvicorn
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
STORE_PATH = DATA_DIR / 'greentv_accounts.json'
PROTOTYPE_PATH = BASE_DIR / 'greentv-media-onboarding-prototype.html'
INSTALL_PORTAL_PATH = BASE_DIR / 'install-business-in-a-box' / 'index.html'
INSTALL_DIRECT_PATH = BASE_DIR / 'install-business-in-a-box.html'
START_HERE_INDEX_PATH = BASE_DIR / '00-START-HERE' / 'index.html'
START_HERE_POPUP_PATH = BASE_DIR / '00-START-HERE' / 'eve-agent-popup.html'
START_HERE_CONFIG_PATH = BASE_DIR / '00-START-HERE' / 'install-config.js'
INSTALLER_DIR = BASE_DIR / 'installer'
INSTALLER_LOGIN_PATH = INSTALLER_DIR / 'login.html'
INSTALLER_INDEX_PATH = INSTALLER_DIR / 'index.html'
INSTALLER_PACKAGE_PATH = INSTALLER_DIR / 'GREENTV_BROADCASTING_KIT_RELEASE_v1.0.0.zip'
INSTALLER_PASSWORD = 'greentvrocks'
INSTALLER_COOKIE = 'greentv_installer_token'
INSTALLER_COOKIE_VALUE = hashlib.sha256(f'greentv-installer::{INSTALLER_PASSWORD}'.encode('utf-8')).hexdigest()


sys.path.append(str(BASE_DIR / 'square-integration'))
from process_payment import process_payment, create_invoice_for_custom_deal  # noqa: E402

app = FastAPI(title='GreenTV', version='1.1.0')


class PaymentRequest(BaseModel):
    source_id: str
    amount_cents: int
    currency: str = 'USD'
    note: str = ''
    customer_id: str | None = None
    location_id: str | None = None


def load_store() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not STORE_PATH.exists():
        return {'users': {}, 'sessions': {}}
    try:
        return json.loads(STORE_PATH.read_text(encoding='utf-8'))
    except Exception:
        return {'users': {}, 'sessions': {}}


def save_store(store: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(json.dumps(store, indent=2, ensure_ascii=False), encoding='utf-8')


def hash_password(password: str, salt: str | None = None) -> dict:
    if salt is None:
        salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 150_000)
    return {'salt': salt, 'hash': digest.hex()}


def verify_password(password: str, salt: str, stored_hash: str) -> bool:
    return hash_password(password, salt)['hash'] == stored_hash


def infer_membership(portal: str, wants_video: bool, role_hint: str) -> str:
    role_hint = (role_hint or '').lower()
    if 'show' in role_hint or 'partner' in role_hint or portal == 'greentv.app':
        return 'Studio'
    if wants_video:
        return 'Creator Pro'
    return 'Community'


def membership_features(level: str) -> list[str]:
    mapping = {
        'Community': [
            'Text posts, links, images, and interview requests',
            'Basic dashboard with submission history',
            'No video uploads yet',
        ],
        'Creator Pro': [
            'Video uploads allowed up to 250 MB per file',
            'H.264 MP4 preferred for low file size and high quality',
            'Priority review for posts and clips',
        ],
        'Studio': [
            'Video uploads and show workflows',
            'H.264 MP4 preferred, efficient bitrate required',
            'Priority review and automation-ready access',
        ],
    }
    return mapping.get(level, mapping['Community'])


def get_user_from_request(request: Request) -> dict | None:
    store = load_store()
    token = request.cookies.get('greentv_session')
    if not token:
        return None
    email = store.get('sessions', {}).get(token)
    if not email:
        return None
    return store.get('users', {}).get(email.lower())


def attach_session(response, email: str) -> None:
    store = load_store()
    token = secrets.token_urlsafe(32)
    store.setdefault('sessions', {})[token] = email.lower()
    save_store(store)
    response.set_cookie(
        'greentv_session',
        token,
        httponly=True,
        samesite='lax',
        max_age=60 * 60 * 24 * 30,
        path='/',
    )


def dashboard_shell(title: str, body: str) -> str:
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
  <style>
    body {{ font-family: Inter, system-ui, sans-serif; background: #F8F5F0; }}
    .heading-font {{ font-family: 'Space Grotesk', Inter, sans-serif; }}
    .green-gradient {{ background: linear-gradient(135deg, #020c09 0%, #1A5F4A 100%); }}
  </style>
</head>
<body class="bg-[#F8F5F0] text-[#1F2A24]">
{body}
</body>
</html>'''


def render_auth_page(message: str = '') -> str:
    msg_html = f'<div class="mb-6 rounded-2xl bg-amber-50 border border-amber-200 p-4 text-sm text-amber-900">{message}</div>' if message else ''
    return dashboard_shell(
        'GreenTV Dashboard Login',
        f'''
<div class="green-gradient text-white">
  <div class="max-w-6xl mx-auto px-6 py-14">
    <div class="max-w-3xl">
      <div class="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-1 text-xs uppercase tracking-[0.25em]">GreenTV Media Dashboard</div>
      <h1 class="heading-font mt-5 text-5xl font-semibold tracking-tight">Create your account, then manage your posts and videos here.</h1>
      <p class="mt-4 max-w-2xl text-lg text-white/80">This page is the real handoff from Mr. Onboarder on greentv.media. Choose your portal, set your membership level, and get your dashboard live.</p>
    </div>
  </div>
</div>

<div class="max-w-6xl mx-auto px-6 py-10 grid gap-8 lg:grid-cols-2">
  <div class="bg-white rounded-3xl shadow-sm border border-gray-200 p-8">
    <h2 class="heading-font text-2xl font-semibold">Create account</h2>
    <p class="mt-2 text-sm text-[#4A5C54]">This creates your greentv.media dashboard login. Your selected portal tells us whether you are headed toward greentv.com WordPress or greentv.app automation.</p>
    {msg_html}
    <form method="post" action="/api/account/create" class="mt-6 space-y-4">
      <div>
        <label class="block text-xs font-semibold mb-1.5">Full name</label>
        <input name="name" required class="w-full rounded-2xl border border-gray-300 px-4 py-3" placeholder="Olivia Green fan / creator / producer">
      </div>
      <div>
        <label class="block text-xs font-semibold mb-1.5">Email</label>
        <input name="email" type="email" required class="w-full rounded-2xl border border-gray-300 px-4 py-3" placeholder="name@example.com">
      </div>
      <div>
        <label class="block text-xs font-semibold mb-1.5">Password</label>
        <input name="password" type="password" required class="w-full rounded-2xl border border-gray-300 px-4 py-3" placeholder="Create a secure password">
      </div>
      <div>
        <label class="block text-xs font-semibold mb-1.5">Where are you going?</label>
        <select name="portal" class="w-full rounded-2xl border border-gray-300 px-4 py-3">
          <option value="greentv.media">greentv.media dashboard</option>
          <option value="greentv.com">greentv.com WordPress login</option>
          <option value="greentv.app">greentv.app app login</option>
        </select>
      </div>
      <div>
        <label class="block text-xs font-semibold mb-1.5">What do you need?</label>
        <select name="role_hint" class="w-full rounded-2xl border border-gray-300 px-4 py-3">
          <option value="creator">Creator / contributor</option>
          <option value="show-owner">TV show owner / producer</option>
          <option value="partner">Partner / sponsor / business</option>
          <option value="community">Community member</option>
        </select>
      </div>
      <label class="flex items-start gap-3 rounded-2xl border border-gray-200 bg-[#F8F5F0] p-4 text-sm">
        <input type="checkbox" name="wants_video" value="1" class="mt-1 accent-[#0F4C3A]">
        <span><strong>Video uploads</strong> enabled if you need them. We keep video quality high and file size efficient: H.264 MP4 preferred.</span>
      </label>
      <button class="w-full rounded-2xl bg-[#0F4C3A] py-3.5 font-semibold text-white">Create account and open dashboard</button>
    </form>
  </div>

  <div class="bg-white rounded-3xl shadow-sm border border-gray-200 p-8">
    <h2 class="heading-font text-2xl font-semibold">Login</h2>
    <p class="mt-2 text-sm text-[#4A5C54]">If you already created an account, log in here and continue to your dashboard.</p>
    <form method="post" action="/api/account/login" class="mt-6 space-y-4">
      <div>
        <label class="block text-xs font-semibold mb-1.5">Email</label>
        <input name="email" type="email" required class="w-full rounded-2xl border border-gray-300 px-4 py-3">
      </div>
      <div>
        <label class="block text-xs font-semibold mb-1.5">Password</label>
        <input name="password" type="password" required class="w-full rounded-2xl border border-gray-300 px-4 py-3">
      </div>
      <button class="w-full rounded-2xl border border-[#0F4C3A] py-3.5 font-semibold text-[#0F4C3A]">Log in</button>
    </form>

    <div class="mt-8 rounded-3xl bg-[#F8F5F0] p-6">
      <div class="text-xs font-semibold uppercase tracking-[0.25em] text-[#C5A46E]">Membership levels</div>
      <div class="mt-3 space-y-3 text-sm">
        <div><strong>Community</strong> — posts, links, images, interview requests</div>
        <div><strong>Creator Pro</strong> — video uploads up to 250 MB, H.264 MP4 preferred</div>
        <div><strong>Studio</strong> — show workflows, automation, priority review</div>
      </div>
    </div>
  </div>
</div>
''',
    )


def render_dashboard_page(user: dict) -> str:
    submissions = user.get('submissions', [])
    features = membership_features(user.get('membership', 'Community'))
    portal = user.get('portal', 'greentv.media')
    portal_button = ''
    if portal == 'greentv.com':
        portal_button = '<a href="https://greentv.com/wp-login.php?redirect_to=https://greentv.media/dashboard" class="rounded-2xl bg-white px-4 py-2 font-semibold text-[#0F4C3A]">Continue with greentv.com WordPress login</a>'
    elif portal == 'greentv.app':
        portal_button = '<a href="https://greentv.app/login?redirect=/dashboard" class="rounded-2xl bg-white px-4 py-2 font-semibold text-[#0F4C3A]">Continue with greentv.app login</a>'
    else:
        portal_button = '<a href="/dashboard" class="rounded-2xl bg-white px-4 py-2 font-semibold text-[#0F4C3A]">Open greentv.media dashboard</a>'

    feature_list = ''.join(f'<li class="flex gap-3"><span class="mt-1 h-2 w-2 rounded-full bg-[#C5A46E]"></span><span>{f}</span></li>' for f in features)
    submission_rows = ''.join(
        f'<div class="rounded-2xl border border-gray-200 p-4"><div class="font-semibold">{item.get("title", "Untitled")}</div><div class="mt-1 text-xs text-[#4A5C54]">{item.get("kind", "Post")} • {item.get("created_at", "")}</div><div class="mt-2 text-sm text-[#4A5C54]">{item.get("notes", "")}</div></div>'
        for item in submissions
    ) or '<div class="rounded-2xl border border-dashed border-gray-300 p-6 text-sm text-[#4A5C54]">No submissions yet. Add your first post, show idea, or video below.</div>'

    return dashboard_shell(
        f'GreenTV Dashboard • {user["name"]}',
        f'''
<div class="green-gradient text-white">
  <div class="max-w-6xl mx-auto px-6 py-12 flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
    <div>
      <div class="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-1 text-xs uppercase tracking-[0.25em]">Signed in</div>
      <h1 class="heading-font mt-4 text-4xl font-semibold tracking-tight">Welcome, {user['name']}</h1>
      <p class="mt-2 text-white/80">Your dashboard is live. Membership: <strong>{user.get('membership', 'Community')}</strong>. Portal: <strong>{portal}</strong>.</p>
    </div>
    <div class="flex gap-3 flex-wrap">{portal_button}
      <form method="post" action="/api/account/logout"><button class="rounded-2xl border border-white/30 px-4 py-2 font-semibold">Log out</button></form>
    </div>
  </div>
</div>

<div class="max-w-6xl mx-auto px-6 py-10 grid gap-8 lg:grid-cols-3">
  <div class="space-y-8 lg:col-span-1">
    <div class="rounded-3xl bg-white border border-gray-200 p-6 shadow-sm">
      <div class="text-xs font-semibold uppercase tracking-[0.25em] text-[#C5A46E]">Account</div>
      <div class="mt-3 text-lg font-semibold">{user['email']}</div>
      <div class="mt-2 text-sm text-[#4A5C54]">Connected portal: {portal}</div>
      <div class="mt-4 text-sm text-[#4A5C54]">Created: {user.get('created_at', '')}</div>
    </div>

    <div class="rounded-3xl bg-white border border-gray-200 p-6 shadow-sm">
      <div class="text-xs font-semibold uppercase tracking-[0.25em] text-[#C5A46E]">Membership access</div>
      <ul class="mt-4 space-y-3 text-sm text-[#1F2A24]">{feature_list}</ul>
      <div class="mt-4 rounded-2xl bg-[#F8F5F0] p-4 text-sm text-[#4A5C54]">If you need video uploads, keep files H.264 MP4 and optimize for low file size with high quality.</div>
    </div>
  </div>

  <div class="space-y-8 lg:col-span-2">
    <div class="rounded-3xl bg-white border border-gray-200 p-6 shadow-sm">
      <div class="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <div class="text-xs font-semibold uppercase tracking-[0.25em] text-[#C5A46E]">Submit a post or video for a show</div>
          <h2 class="heading-font mt-2 text-2xl font-semibold">Dashboard intake</h2>
        </div>
      </div>
      <form method="post" action="/api/submissions" class="mt-6 grid gap-4 md:grid-cols-2">
        <div class="md:col-span-2">
          <label class="block text-xs font-semibold mb-1.5">Title</label>
          <input name="title" required class="w-full rounded-2xl border border-gray-300 px-4 py-3" placeholder="Episode idea, post title, or clip name">
        </div>
        <div>
          <label class="block text-xs font-semibold mb-1.5">Type</label>
          <select name="kind" class="w-full rounded-2xl border border-gray-300 px-4 py-3">
            <option value="Post">Post</option>
            <option value="Video">Video</option>
            <option value="Show pitch">Show pitch</option>
            <option value="Interview request">Interview request</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-semibold mb-1.5">Source URL / file link</label>
          <input name="link" class="w-full rounded-2xl border border-gray-300 px-4 py-3" placeholder="https://...">
        </div>
        <div class="md:col-span-2">
          <label class="block text-xs font-semibold mb-1.5">Notes</label>
          <textarea name="notes" rows="4" class="w-full rounded-2xl border border-gray-300 px-4 py-3" placeholder="Add context, deadlines, format details, or upload notes."></textarea>
        </div>
        <div class="md:col-span-2">
          <button class="rounded-2xl bg-[#0F4C3A] px-5 py-3 font-semibold text-white">Save to dashboard</button>
        </div>
      </form>
    </div>

    <div class="rounded-3xl bg-white border border-gray-200 p-6 shadow-sm">
      <div class="text-xs font-semibold uppercase tracking-[0.25em] text-[#C5A46E]">Your submissions</div>
      <div class="mt-4 grid gap-4">{submission_rows}</div>
    </div>
  </div>
</div>
''',
    )


@app.api_route('/', methods=['GET', 'HEAD'], response_class=HTMLResponse)
async def main_page():
    if PROTOTYPE_PATH.exists():
        return HTMLResponse(PROTOTYPE_PATH.read_text(encoding='utf-8'))
    return HTMLResponse('<h1>GreenTV prototype not found</h1>', status_code=404)


@app.get('/install-business-in-a-box')
async def install_business_in_a_box():
    if INSTALL_PORTAL_PATH.exists():
        return FileResponse(INSTALL_PORTAL_PATH)
    return HTMLResponse('<h1>Installer portal not found</h1>', status_code=404)


@app.get('/install-business-in-a-box/index.html')
async def install_business_in_a_box_index():
    if INSTALL_PORTAL_PATH.exists():
        return FileResponse(INSTALL_PORTAL_PATH)
    return HTMLResponse('<h1>Installer portal not found</h1>', status_code=404)


@app.get('/install-business-in-a-box/')
async def install_business_in_a_box_slash():
    return RedirectResponse('/install-business-in-a-box', status_code=301)


@app.get('/install-business-in-a-box.html')
async def install_business_in_a_box_direct():
    if INSTALL_DIRECT_PATH.exists():
        return FileResponse(INSTALL_DIRECT_PATH)
    return HTMLResponse('<h1>Installer direct link not found</h1>', status_code=404)


@app.get('/00-START-HERE/index.html')
async def start_here_index():
    if START_HERE_INDEX_PATH.exists():
        return FileResponse(START_HERE_INDEX_PATH)
    return HTMLResponse('<h1>Start Here index not found</h1>', status_code=404)


@app.get('/00-START-HERE/eve-agent-popup.html')
async def start_here_popup():
    if START_HERE_POPUP_PATH.exists():
        return FileResponse(START_HERE_POPUP_PATH)
    return HTMLResponse('<h1>Eve agent popup not found</h1>', status_code=404)


@app.get('/00-START-HERE/install-config.js')
async def start_here_config():
    if START_HERE_CONFIG_PATH.exists():
        return FileResponse(START_HERE_CONFIG_PATH, media_type='application/javascript')
    return HTMLResponse('// install-config.js not found', status_code=404, media_type='application/javascript')


@app.get('/dashboard', response_class=HTMLResponse)
async def dashboard(request: Request):
    user = get_user_from_request(request)
    if not user:
        return HTMLResponse(render_auth_page())
    return HTMLResponse(render_dashboard_page(user))


@app.post('/api/account/create')
async def create_account(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    portal: str = Form('greentv.media'),
    role_hint: str = Form('community'),
    wants_video: str | None = Form(None),
):
    store = load_store()
    email_key = email.strip().lower()
    if email_key in store.get('users', {}):
        response = RedirectResponse('/dashboard', status_code=303)
        attach_session(response, email_key)
        return response

    password_data = hash_password(password)
    membership = infer_membership(portal, wants_video is not None, role_hint)
    user = {
        'name': name.strip(),
        'email': email_key,
        'portal': portal,
        'membership': membership,
        'created_at': datetime.utcnow().isoformat(timespec='seconds') + 'Z',
        'password_salt': password_data['salt'],
        'password_hash': password_data['hash'],
        'submissions': [],
    }
    store.setdefault('users', {})[email_key] = user
    save_store(store)
    response = RedirectResponse('/dashboard', status_code=303)
    attach_session(response, email_key)
    return response


@app.post('/api/account/login')
async def login_account(email: str = Form(...), password: str = Form(...)):
    store = load_store()
    email_key = email.strip().lower()
    user = store.get('users', {}).get(email_key)
    if not user or not verify_password(password, user.get('password_salt', ''), user.get('password_hash', '')):
        return HTMLResponse(render_auth_page('Invalid email or password. Please try again.'), status_code=401)
    response = RedirectResponse('/dashboard', status_code=303)
    attach_session(response, email_key)
    return response


@app.post('/api/account/logout')
async def logout_account(request: Request):
    store = load_store()
    token = request.cookies.get('greentv_session')
    if token and token in store.get('sessions', {}):
        del store['sessions'][token]
        save_store(store)
    response = RedirectResponse('/dashboard', status_code=303)
    response.delete_cookie('greentv_session', path='/')
    return response


@app.post('/api/submissions')
async def create_submission(
    request: Request,
    title: str = Form(...),
    kind: str = Form('Post'),
    link: str = Form(''),
    notes: str = Form(''),
):
    store = load_store()
    token = request.cookies.get('greentv_session')
    email = store.get('sessions', {}).get(token)
    if not email:
        raise HTTPException(status_code=401, detail='Not signed in')
    user = store.get('users', {}).get(email)
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    submission = {
        'title': title.strip(),
        'kind': kind,
        'link': link.strip(),
        'notes': notes.strip(),
        'created_at': datetime.utcnow().isoformat(timespec='seconds') + 'Z',
    }
    user.setdefault('submissions', []).insert(0, submission)
    store['users'][email] = user
    save_store(store)
    return RedirectResponse('/dashboard', status_code=303)


@app.post('/api/process-payment')
async def api_process_payment(request: PaymentRequest):
    try:
        result = process_payment(
            source_id=request.source_id,
            amount_cents=request.amount_cents,
            currency=request.currency,
            note=request.note,
            customer_id=request.customer_id,
            location_id=request.location_id,
        )
        if result.get('success'):
            payment = result.get('payment')
            return {
                'success': True,
                'payment_id': getattr(payment, 'id', None),
                'status': getattr(payment, 'status', None),
                'amount': getattr(payment, 'amount_money', {}).get('amount', request.amount_cents),
            }
        raise HTTPException(status_code=400, detail=result.get('errors', 'Payment failed'))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/create-invoice')
async def api_create_invoice(
    customer_email: str = Form(...),
    amount_cents: int = Form(...),
    description: str = Form(...),
    due_date: str | None = Form(None),
):
    try:
        return create_invoice_for_custom_deal(
            customer_email=customer_email,
            amount_cents=amount_cents,
            description=description,
            due_date=due_date,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/installer')
@app.get('/installer/')
@app.get('/installer/index.html')
async def installer_home(request: Request):
    if not INSTALLER_INDEX_PATH.exists():
        return HTMLResponse('<h1>Installer page not found</h1>', status_code=404)
    if request.cookies.get(INSTALLER_COOKIE) == INSTALLER_COOKIE_VALUE:
        return FileResponse(INSTALLER_INDEX_PATH)
    return FileResponse(INSTALLER_LOGIN_PATH) if INSTALLER_LOGIN_PATH.exists() else HTMLResponse('<h1>Installer login page not found</h1>', status_code=404)


@app.post('/installer/unlock')
async def installer_unlock(password: str = Form(...)):
    if password == INSTALLER_PASSWORD:
        response = RedirectResponse('/installer', status_code=303)
        response.set_cookie(INSTALLER_COOKIE, INSTALLER_COOKIE_VALUE, httponly=True, samesite='lax', max_age=60 * 60 * 24 * 7, path='/')
        return response
    return RedirectResponse('/installer', status_code=303)


@app.get('/installer/download')
async def installer_download(request: Request):
    if request.cookies.get(INSTALLER_COOKIE) != INSTALLER_COOKIE_VALUE:
        return RedirectResponse('/installer', status_code=303)
    if INSTALLER_PACKAGE_PATH.exists():
        return FileResponse(INSTALLER_PACKAGE_PATH, filename='GREENTV_BROADCASTING_KIT_RELEASE_v1.0.0.zip')
    return HTMLResponse('<h1>Installer package not uploaded yet</h1>', status_code=404)


@app.get('/installer/logout')
async def installer_logout():
    response = RedirectResponse('/installer', status_code=303)
    response.delete_cookie(INSTALLER_COOKIE, path='/')
    return response


@app.get('/health')
async def health():
    return {'status': 'ok', 'service': 'greentv-media'}


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
