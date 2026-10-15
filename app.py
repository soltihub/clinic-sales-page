"""Clinic ad-copy sales page + free-sample form + protected admin view.
Run: ADMIN_PASSWORD='choose-a-strong-one' python3 app.py   (port 8080)
Portfolio videos: drop MP4s into ./videos named ad1.mp4 ... ad5.mp4
"""
import os, re, html, sqlite3, secrets, base64, json, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.environ.get("DB_PATH", os.path.join(ROOT, "submissions.db"))
ADMIN_USER = "admin"
ADMIN_PASS = os.environ.get("ADMIN_PASSWORD", "")
MAX_BODY = 10_000

def db():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS subs(id INTEGER PRIMARY KEY, ts TEXT, name TEXT,
      clinic TEXT, email TEXT, phone TEXT, emirate TEXT, specialty TEXT, goal TEXT, status TEXT DEFAULT 'new')""")
    return c

EMIRATES = ["Abu Dhabi","Dubai","Sharjah","Ajman","Umm Al Quwain","Ras Al Khaimah","Fujairah"]
SPECIALTIES = ["Dental","Dermatology","Cosmetic / aesthetic","Physiotherapy","IVF / fertility","General practice","Other"]

def validate(f):
    g = lambda k: (f.get(k, [""])[0]).strip()
    d = {k: g(k) for k in ["name","clinic","email","phone","emirate","specialty","goal","website","consent"]}
    err = {}
    if d["website"]: err["_"] = "Spam detected."  # honeypot
    if not (2 <= len(d["name"]) <= 80) or not re.fullmatch(r"[\w\s.'\-\u0600-\u06FF]+", d["name"]): err["name"] = "Please enter your name (2–80 letters)."
    if not (2 <= len(d["clinic"]) <= 120): err["clinic"] = "Please enter your clinic name."
    if not re.fullmatch(r"[^@\s]{1,64}@[^@\s]+\.[A-Za-z]{2,}", d["email"]) or len(d["email"]) > 120: err["email"] = "Please enter a valid email."
    ph = re.sub(r"[\s\-()]", "", d["phone"])
    if not re.fullmatch(r"(\+971|00971|0)?5\d{8}|(\+971|00971|0)?[2-9]\d{7}", ph): err["phone"] = "Please enter a valid UAE phone number."
    if d["emirate"] not in EMIRATES: err["emirate"] = "Please choose an emirate."
    if d["specialty"] not in SPECIALTIES: err["specialty"] = "Please choose a specialty."
    if not (10 <= len(d["goal"]) <= 600): err["goal"] = "Tell us about the service you want to promote (10–600 characters)."
    if d["consent"] != "yes": err["consent"] = "Please agree so we can contact you."
    d["phone"] = ph
    return d, err

CTA = '<div class="cta"><a class="btn" href="#sample">Get my free sample ad</a><p>Free, no obligation. A real person replies within 2 working days.</p></div>'

def video(i, title):
    p = os.path.join(ROOT, "videos", f"ad{i}.mp4")
    if os.path.exists(p):
        media = f'<video controls playsinline preload="metadata" src="/videos/ad{i}.mp4"></video>'
    else:
        media = '<div class="ph">Video coming soon</div>'
    return f'<figure>{media}<figcaption>{title}</figcaption></figure>'

def page(errors=None, values=None, ok=False):
    e = errors or {}; v = values or {}
    val = lambda k: html.escape(v.get(k, ""))
    er = lambda k: f'<span class="err">{html.escape(e[k])}</span>' if k in e else ""
    opts = lambda lst, k: "".join(f'<option{" selected" if v.get(k)==o else ""}>{html.escape(o)}</option>' for o in lst)
    form = ('<p class="okmsg">Thank you! Your request is in. A real person will review it and reply within 2 working days.</p>' if ok else f"""
<form method="post" action="/#sample" novalidate>
 {er('_')}
 <label>Your name<input name="name" maxlength="80" required value="{val('name')}"></label>{er('name')}
 <label>Clinic name<input name="clinic" maxlength="120" required value="{val('clinic')}"></label>{er('clinic')}
 <label>Email<input type="email" name="email" maxlength="120" required value="{val('email')}"></label>{er('email')}
 <label>UAE phone / WhatsApp<input type="tel" name="phone" maxlength="20" required placeholder="05X XXX XXXX" value="{val('phone')}"></label>{er('phone')}
 <label>Emirate<select name="emirate" required><option value="">Choose…</option>{opts(EMIRATES,'emirate')}</select></label>{er('emirate')}
 <label>Specialty<select name="specialty" required><option value="">Choose…</option>{opts(SPECIALTIES,'specialty')}</select></label>{er('specialty')}
 <label>Which service do you want more bookings for?<textarea name="goal" maxlength="600" required>{val('goal')}</textarea></label>{er('goal')}
 <input class="hp" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">
 <label class="chk"><input type="checkbox" name="consent" value="yes"{" checked" if v.get('consent')=='yes' else ""}> I agree to be contacted about my free sample.</label>{er('consent')}
 <button class="btn" type="submit">Send my request</button>
</form>""")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Clinic ad copy for UAE clinics</title><style>
*{{box-sizing:border-box}}body{{margin:0;font-family:system-ui,Segoe UI,Arial,sans-serif;color:#1d2433;line-height:1.6;background:#fbf8f3}}
section{{padding:56px 20px;max-width:1040px;margin:auto}}h1{{font-size:clamp(28px,5vw,46px);line-height:1.15;margin:0 0 16px}}h2{{font-size:clamp(22px,3.5vw,32px)}}
.hero{{background:#13284a;color:#fff;max-width:none}}.hero>div{{max-width:1040px;margin:auto}}.price{{background:#c9a24a22;border-left:4px solid #c9a24a;padding:12px 16px;margin:20px 0}}
.btn{{display:inline-block;background:#c9a24a;color:#13284a;font-weight:700;padding:14px 26px;border-radius:8px;text-decoration:none;border:0;font-size:16px;cursor:pointer}}
.cta{{text-align:center;margin-top:32px}}.cta p{{font-size:14px;opacity:.75}}.grid{{display:grid;gap:20px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}}
figure{{margin:0;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 2px 10px #0001}}video,.ph{{width:100%;aspect-ratio:16/9;display:block;background:#000}}
.ph{{display:flex;align-items:center;justify-content:center;color:#fff;background:#2a3b5c}}figcaption{{padding:10px 14px;font-size:14px}}
.card{{background:#fff;padding:20px;border-radius:10px;box-shadow:0 2px 10px #0001}}details{{background:#fff;margin:10px 0;padding:14px 18px;border-radius:8px}}summary{{font-weight:600;cursor:pointer}}
form{{display:grid;gap:10px;max-width:560px;margin:auto}}label{{display:grid;gap:4px;font-weight:600}}input,select,textarea{{font:inherit;padding:10px;border:1px solid #c8ccd4;border-radius:6px}}textarea{{min-height:100px}}
.chk{{display:flex;gap:8px;font-weight:400}}.err{{color:#b00020;font-size:14px}}.hp{{position:absolute;left:-9999px}}.okmsg{{background:#e6f4ea;padding:16px;border-radius:8px;text-align:center}}
.small{{font-size:13px;opacity:.75}}</style></head><body>

<section class="hero"><div>
<h1>Ad copy that UAE clinics can get approved, and that brings in bookings</h1>
<p>I write social ads, Google Ads and landing page copy for private clinics across the UAE: dental, dermatology, aesthetics, physiotherapy and more. The goal is clear, compliant ads that turn views into appointments.</p>
<div class="price"><strong>Launch offer: a starter ad pack for AED 550</strong>, including 3 social ad variations, 1 Google Ads set and 1 round of edits.<br>
Why so low? I'm taking on my first clinic clients and want to build case studies. This launch price is for the first 5 clinics only.</div>
<a class="btn" href="#sample">Get my free sample ad</a></div></section>

<section id="work"><h2>Work</h2><p>Sample video ad concepts. These are sample work, not paid client campaigns, and every actor shown is a performer, not a patient.</p>
<div class="grid">{video(1,"Cinematic before-and-after (of the ad, not a patient)")}{video(2,"Funny: 'Rejected… again?!'")}{video(3,"Fictional scenario, clearly labelled")}{video(4,"Problem-focused")}{video(5,"Premium brand")}</div>{CTA}</section>

<section id="process"><h2>Process</h2><div class="grid">
<div class="card"><h3>1. Answer a few quick questions</h3><p>Your clinic, specialty, emirate and the service you want more bookings for. It takes about 2 minutes.</p></div>
<div class="card"><h3>2. A real person reviews it</h3><p>Every request is read by me, not an automated system. I check your offer and current ads.</p></div>
<div class="card"><h3>3. Get your free sample</h3><p>You receive one sample ad written for your clinic within 2 working days. You decide if you want more.</p></div></div>
<p class="small">Clinics must get their own advertising approvals (for example from MOHAP or DHA) before publishing. I write copy with those rules in mind, but I can't apply for approvals on your behalf or guarantee them.</p>{CTA}</section>

<section id="benefits"><h2>Benefits</h2><div class="grid">
<div class="card"><h3>Written with UAE healthcare ad rules in mind</h3><p>No guaranteed outcomes, no fake testimonials and no misleading claims, all of which are common reasons ads get sent back.</p></div>
<div class="card"><h3>One clear offer per ad</h3><p>Each ad has one service, one reason to book and one call to action.</p></div>
<div class="card"><h3>Ready-to-use formats</h3><p>Copy is delivered for Instagram, Facebook, Google Ads and your landing page.</p></div></div>
<p class="small">Not included: your ad spend on Meta or Google, MOHAP/DHA licence fees, design or video production, or translation into Arabic, unless agreed separately.</p>{CTA}</section>

<section id="faq"><h2>FAQ</h2>
<details><summary>Will my ads definitely get approved?</summary><p>No one can promise that. Approval is decided by the authorities. What I can do is write copy that avoids the issues that most often get ads rejected.</p></details>
<details><summary>Can you guarantee more bookings?</summary><p>No. Results depend on your offer, budget, targeting and front desk. I focus on making the copy as clear and persuasive as possible.</p></details>
<details><summary>Do you have clinic case studies yet?</summary><p>Not yet, which is why there's a launch price. The videos above are sample work, and your free sample shows my style before you pay anything.</p></details>
<details><summary>Do you write in Arabic?</summary><p>The copy is written in English. Arabic can be arranged through a translator for an extra fee.</p></details>
<details><summary>What does the free sample include?</summary><p>One ad written for one of your services, with no payment details needed and no obligation.</p></details>
<details><summary>What happens to my details?</summary><p>They're used only to prepare your sample and contact you about it. They are never sold or shared.</p></details>
{CTA}</section>

<section id="sample"><h2>Get your free sample ad</h2>{form}</section>
</body></html>"""

def admin_page():
    rows = db().execute("SELECT id,ts,name,clinic,email,phone,emirate,specialty,goal,status FROM subs ORDER BY id DESC").fetchall()
    tr = "".join("<tr>"+"".join(f"<td>{html.escape(str(c))}</td>" for c in r)+
        f'<td><form method="post" action="/admin/status"><input type="hidden" name="id" value="{r[0]}"><select name="status">'+
        "".join(f'<option{" selected" if r[9]==s else ""}>{s}</option>' for s in ["new","reviewed","contacted","rejected"])+
        '</select><button>Save</button></form></td></tr>' for r in rows)
    return f"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Admin</title>
<style>body{{font-family:system-ui;padding:20px}}table{{border-collapse:collapse;width:100%;font-size:14px}}td,th{{border:1px solid #ddd;padding:6px;vertical-align:top}}</style>
<h1>Free-sample requests ({len(rows)})</h1><p>Review each request by hand before contacting anyone.</p>
<div style="overflow-x:auto"><table><tr><th>ID</th><th>Time (UAE)</th><th>Name</th><th>Clinic</th><th>Email</th><th>Phone</th><th>Emirate</th><th>Specialty</th><th>Goal</th><th>Status</th><th>Update</th></tr>{tr}</table></div>"""

HITS = {}
class H(BaseHTTPRequestHandler):
    def send(self, code, body, ctype="text/html; charset=utf-8", extra=None):
        b = body.encode() if isinstance(body, str) else body
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(b)))
        self.send_header("X-Content-Type-Options","nosniff"); self.send_header("X-Frame-Options","DENY")
        self.send_header("Content-Security-Policy","default-src 'self'; style-src 'self' 'unsafe-inline'; media-src 'self'")
        for k, v in (extra or {}).items(): self.send_header(k, v)
        self.end_headers(); self.wfile.write(b)
    def authed(self):
        if not ADMIN_PASS: return False
        a = self.headers.get("Authorization", "")
        if not a.startswith("Basic "): return False
        try: u, p = base64.b64decode(a[6:]).decode().split(":", 1)
        except Exception: return False
        return secrets.compare_digest(u, ADMIN_USER) and secrets.compare_digest(p, ADMIN_PASS)
    def deny(self): self.send(401, "Login required", "text/plain", {"WWW-Authenticate": 'Basic realm="admin"'})
    def body(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        if n > MAX_BODY: return None
        return parse_qs(self.rfile.read(n).decode("utf-8", "replace"))
    def do_GET(self):
        p = self.path.split("?")[0]
        if p == "/": return self.send(200, page())
        if p.startswith("/videos/") and re.fullmatch(r"/videos/ad[1-5]\.mp4", p):
            f = os.path.join(ROOT, p.lstrip("/"))
            if os.path.exists(f): return self.send(200, open(f, "rb").read(), "video/mp4")
        if p == "/admin": return self.send(200, admin_page()) if self.authed() else self.deny()
        self.send(404, "Not found", "text/plain")
    def do_POST(self):
        p = self.path.split("?")[0].split("#")[0]
        if p == "/admin/status":
            if not self.authed(): return self.deny()
            f = self.body() or {}
            sid, st = f.get("id", [""])[0], f.get("status", [""])[0]
            if sid.isdigit() and st in ["new","reviewed","contacted","rejected"]:
                c = db(); c.execute("UPDATE subs SET status=? WHERE id=?", (st, int(sid))); c.commit()
            return self.send(303, "", extra={"Location": "/admin"})
        if p == "/":
            ip = self.client_address[0]; now = time.time()
            HITS[ip] = [t for t in HITS.get(ip, []) if now - t < 600] + [now]
            if len(HITS[ip]) > 5: return self.send(429, "Too many requests, please try later.", "text/plain")
            f = self.body()
            if f is None: return self.send(413, "Too large", "text/plain")
            d, err = validate(f)
            if err: return self.send(400, page(err, d))
            c = db(); c.execute("INSERT INTO subs(ts,name,clinic,email,phone,emirate,specialty,goal) VALUES(?,?,?,?,?,?,?,?)",
                (time.strftime("%Y-%m-%d %H:%M"), d["name"], d["clinic"], d["email"], d["phone"], d["emirate"], d["specialty"], d["goal"])); c.commit()
            return self.send(200, page(ok=True))
        self.send(404, "Not found", "text/plain")

if __name__ == "__main__":
    if not ADMIN_PASS: print("WARNING: set ADMIN_PASSWORD; admin view stays locked until you do.")
    db(); ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", 8080))), H).serve_forever()
