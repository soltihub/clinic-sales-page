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
 <div class="two"><div><label>Email<input type="email" name="email" maxlength="120" required value="{val('email')}"></label>{er('email')}</div>
 <div><label>UAE phone / WhatsApp<input type="tel" name="phone" maxlength="20" required placeholder="05X XXX XXXX" value="{val('phone')}"></label>{er('phone')}</div></div>
 <div class="two"><div><label>Emirate<select name="emirate" required><option value="">Choose…</option>{opts(EMIRATES,'emirate')}</select></label>{er('emirate')}</div>
 <div><label>Specialty<select name="specialty" required><option value="">Choose…</option>{opts(SPECIALTIES,'specialty')}</select></label>{er('specialty')}</div></div>
 <label>Which service do you want more bookings for?<textarea name="goal" maxlength="600" required>{val('goal')}</textarea></label>{er('goal')}
 <input class="hp" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">
 <label class="chk"><input type="checkbox" name="consent" value="yes"{" checked" if v.get('consent')=='yes' else ""}> I agree to be contacted about my free sample.</label>{er('consent')}
 <button class="btn" type="submit">Send my request</button>
</form>""")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Clinic Ads UAE | Compliant ad copy for UAE clinics</title><meta name="description" content="Social ads, Google Ads and landing page copy for private clinics across the UAE. Get a free sample ad.">
<style>
:root{{--navy:#0f2140;--navy2:#1a3260;--gold:#c9a24a;--gold2:#e2c27a;--ink:#1d2433;--muted:#5b6475;--bg:#faf7f2;--line:#e7e1d6}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;font-family:"Segoe UI",system-ui,-apple-system,Roboto,Arial,sans-serif;color:var(--ink);line-height:1.65;background:var(--bg)}}
a{{color:inherit}}h1,h2,h3{{line-height:1.2;letter-spacing:-.01em}}h2{{font-size:clamp(26px,3.6vw,36px);margin:0 0 10px}}h3{{font-size:18px;margin:0 0 8px}}
.wrap{{max-width:1100px;margin:auto;padding:0 22px}}section{{padding:84px 0}}
.eyebrow{{display:inline-block;font-size:12px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--gold)}}
.lead{{color:var(--muted);max-width:640px;margin:0 0 34px}}
nav{{position:sticky;top:0;z-index:10;background:#0f2140ee;backdrop-filter:blur(8px);border-bottom:1px solid #ffffff14}}
nav .wrap{{display:flex;align-items:center;justify-content:space-between;height:64px}}.logo{{color:#fff;font-weight:800;text-decoration:none;font-size:18px}}.logo span{{color:var(--gold)}}
.links{{display:flex;gap:26px;align-items:center}}.links a{{color:#ffffffcc;text-decoration:none;font-size:15px}}.links a:hover{{color:#fff}}
.btn{{display:inline-block;background:linear-gradient(135deg,var(--gold2),var(--gold));color:var(--navy);font-weight:700;padding:15px 28px;border-radius:999px;text-decoration:none;border:0;font-size:16px;cursor:pointer;box-shadow:0 8px 24px #c9a24a40;transition:transform .15s,box-shadow .15s}}
.btn:hover{{transform:translateY(-2px);box-shadow:0 12px 30px #c9a24a59}}.btn.sm{{padding:9px 18px;font-size:14px;box-shadow:none}}
.ghost{{display:inline-block;color:#fff;padding:15px 22px;text-decoration:none;font-weight:600}}
.hero{{background:radial-gradient(1100px 500px at 85% -10%,#2b4f8f 0,transparent 60%),linear-gradient(160deg,var(--navy) 0,var(--navy2) 100%);color:#fff;padding:96px 0 104px}}
.hero .wrap{{display:grid;gap:48px;grid-template-columns:1.25fr .9fr;align-items:center}}
.hero h1{{font-size:clamp(32px,5vw,54px);margin:14px 0 18px}}.hero h1 em{{font-style:normal;color:var(--gold2)}}.hero p{{color:#ffffffd0;font-size:18px;margin:0 0 28px}}
.offer{{background:#ffffff0f;border:1px solid #ffffff26;border-radius:20px;padding:28px;backdrop-filter:blur(6px)}}
.offer .tag{{display:inline-block;background:var(--gold);color:var(--navy);font-size:12px;font-weight:800;padding:4px 10px;border-radius:999px;letter-spacing:.06em}}
.offer .amt{{font-size:44px;font-weight:800;margin:12px 0 2px}}.offer .amt small{{font-size:16px;font-weight:600;opacity:.75}}
.offer ul{{list-style:none;padding:0;margin:16px 0}}.offer li{{padding:8px 0 8px 28px;position:relative;border-top:1px solid #ffffff1a}}.offer li:before{{content:"✓";position:absolute;left:0;color:var(--gold2);font-weight:800}}
.offer .note{{font-size:13px;color:#ffffffa8;margin:0}}
.strip{{background:#fff;border-bottom:1px solid var(--line)}}.strip .wrap{{display:flex;flex-wrap:wrap;gap:12px 34px;justify-content:center;padding:20px 22px;font-size:14px;color:var(--muted)}}.strip b{{color:var(--ink)}}
.grid{{display:grid;gap:22px;grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}}
figure{{margin:0;background:#fff;border-radius:16px;overflow:hidden;border:1px solid var(--line);transition:transform .2s,box-shadow .2s}}figure:hover{{transform:translateY(-4px);box-shadow:0 18px 40px #0f21401a}}
video,.ph{{width:100%;aspect-ratio:16/9;display:block;background:#000}}.ph{{display:flex;align-items:center;justify-content:center;color:#ffffffb0;background:linear-gradient(135deg,var(--navy),#2b4f8f);font-size:14px;letter-spacing:.04em}}
figcaption{{padding:14px 18px;font-size:15px;font-weight:600}}
.card{{background:#fff;padding:28px;border-radius:16px;border:1px solid var(--line)}}.num{{display:inline-flex;width:40px;height:40px;border-radius:12px;align-items:center;justify-content:center;background:#c9a24a22;color:#9a7a2c;font-weight:800;margin-bottom:14px}}
.card p{{color:var(--muted);margin:0}}.alt{{background:#fff}}.alt .card{{background:var(--bg)}}
.small{{font-size:13px;color:var(--muted);margin-top:22px}}
.cta{{text-align:center;margin-top:44px}}.cta p{{font-size:14px;color:var(--muted);margin:10px 0 0}}
.faq{{max-width:800px}}details{{background:#fff;margin:12px 0;padding:18px 22px;border-radius:14px;border:1px solid var(--line)}}summary{{font-weight:650;cursor:pointer;list-style:none;display:flex;justify-content:space-between;gap:12px}}summary:after{{content:"+";color:var(--gold);font-size:22px;line-height:1}}details[open] summary:after{{content:"–"}}details p{{color:var(--muted);margin:12px 0 0}}
.formbox{{background:linear-gradient(160deg,var(--navy),var(--navy2));color:#fff;border-radius:24px;padding:48px 22px;}}.formbox h2{{text-align:center}}.formbox .lead{{text-align:center;margin:0 auto 30px;color:#ffffffc0}}
form{{display:grid;gap:14px;max-width:620px;margin:auto;background:#fff;color:var(--ink);padding:30px;border-radius:18px;box-shadow:0 20px 50px #0003}}
.two{{display:grid;gap:14px;grid-template-columns:1fr 1fr}}label{{display:grid;gap:6px;font-weight:600;font-size:14px}}
input,select,textarea{{font:inherit;padding:12px 14px;border:1px solid #d6d9e0;border-radius:10px;background:#fff;width:100%}}input:focus,select:focus,textarea:focus{{outline:none;border-color:var(--gold);box-shadow:0 0 0 3px #c9a24a33}}textarea{{min-height:110px}}
.chk{{display:flex;gap:10px;font-weight:400;align-items:center}}.chk input{{width:auto}}.err{{color:#b00020;font-size:13px;font-weight:500}}.hp{{position:absolute;left:-9999px}}
form .btn{{width:100%;margin-top:6px}}.okmsg{{background:#e6f4ea;color:#14532d;padding:22px;border-radius:14px;text-align:center;max-width:620px;margin:auto;font-weight:600}}
footer{{padding:34px 0;text-align:center;font-size:13px;color:var(--muted)}}
@media(max-width:820px){{.hero .wrap{{grid-template-columns:1fr}}.links a:not(.btn){{display:none}}.two{{grid-template-columns:1fr}}section{{padding:64px 0}}.hero{{padding:64px 0 72px}}form{{padding:22px}}}}
</style></head><body>

<nav><div class="wrap"><a class="logo" href="#">Clinic Ads <span>UAE</span></a><div class="links"><a href="#work">Work</a><a href="#process">Process</a><a href="#faq">FAQ</a><a class="btn sm" href="#sample">Free sample</a></div></div></nav>

<header class="hero"><div class="wrap"><div>
<span class="eyebrow">Ad copy for UAE private clinics</span>
<h1>Ad copy UAE clinics can get approved, <em>and that brings in bookings</em></h1>
<p>I write social ads, Google Ads and landing page copy for private clinics across the UAE: dental, dermatology, aesthetics, physiotherapy and more. The goal is clear, compliant ads that turn views into appointments.</p>
<a class="btn" href="#sample">Get my free sample ad</a><a class="ghost" href="#work">See sample work →</a></div>
<aside class="offer"><span class="tag">LAUNCH OFFER</span><div class="amt">AED 550 <small>starter ad pack</small></div>
<ul><li>3 social ad variations</li><li>1 Google Ads set</li><li>1 round of edits</li></ul>
<p class="note">Why so low? I'm taking on my first clinic clients and want to build case studies. This launch price is for the first 5 clinics only.</p></aside>
</div></header>

<div class="strip"><div class="wrap"><span><b>Free</b> sample, no obligation</span><span><b>2 working days</b> to reply</span><span>Reviewed by <b>a real person</b></span><span>Written with <b>UAE ad rules</b> in mind</span></div></div>

<section id="work"><div class="wrap"><span class="eyebrow">Work</span><h2>Sample video ad concepts</h2><p class="lead">These are sample work, not paid client campaigns, and every actor shown is a performer, not a patient.</p>
<div class="grid">{video(1,"Cinematic before-and-after (of the ad, not a patient)")}{video(2,"Funny: 'Rejected… again?!'")}{video(3,"Fictional scenario, clearly labelled")}{video(4,"Problem-focused")}{video(5,"Premium brand")}</div>{CTA}</div></section>

<section id="process" class="alt"><div class="wrap"><span class="eyebrow">Process</span><h2>How it works</h2><p class="lead">Three simple steps, and the sample costs you nothing.</p><div class="grid">
<div class="card"><div class="num">1</div><h3>Answer a few quick questions</h3><p>Your clinic, specialty, emirate and the service you want more bookings for. It takes about 2 minutes.</p></div>
<div class="card"><div class="num">2</div><h3>A real person reviews it</h3><p>Every request is read by me, not an automated system. I check your offer and current ads.</p></div>
<div class="card"><div class="num">3</div><h3>Get your free sample</h3><p>You receive one sample ad written for your clinic within 2 working days. You decide if you want more.</p></div></div>
<p class="small">Clinics must get their own advertising approvals (for example from MOHAP or DHA) before publishing. I write copy with those rules in mind, but I can't apply for approvals on your behalf or guarantee them.</p>{CTA}</div></section>

<section id="benefits"><div class="wrap"><span class="eyebrow">Benefits</span><h2>Why clinics work with me</h2><p class="lead">Copy that respects the rules and still gives people a reason to book.</p><div class="grid">
<div class="card"><div class="num">✓</div><h3>Written with UAE healthcare ad rules in mind</h3><p>No guaranteed outcomes, no fake testimonials and no misleading claims, all of which are common reasons ads get sent back.</p></div>
<div class="card"><div class="num">✓</div><h3>One clear offer per ad</h3><p>Each ad has one service, one reason to book and one call to action.</p></div>
<div class="card"><div class="num">✓</div><h3>Ready-to-use formats</h3><p>Copy is delivered for Instagram, Facebook, Google Ads and your landing page.</p></div></div>
<p class="small">Not included: your ad spend on Meta or Google, MOHAP/DHA licence fees, design or video production, or translation into Arabic, unless agreed separately.</p>{CTA}</div></section>

<section id="faq" class="alt"><div class="wrap faq"><span class="eyebrow">FAQ</span><h2>Common questions</h2>
<details><summary>Will my ads definitely get approved?</summary><p>No one can promise that. Approval is decided by the authorities. What I can do is write copy that avoids the issues that most often get ads rejected.</p></details>
<details><summary>Can you guarantee more bookings?</summary><p>No. Results depend on your offer, budget, targeting and front desk. I focus on making the copy as clear and persuasive as possible.</p></details>
<details><summary>Do you have clinic case studies yet?</summary><p>Not yet, which is why there's a launch price. The videos above are sample work, and your free sample shows my style before you pay anything.</p></details>
<details><summary>Do you write in Arabic?</summary><p>The copy is written in English. Arabic can be arranged through a translator for an extra fee.</p></details>
<details><summary>What does the free sample include?</summary><p>One ad written for one of your services, with no payment details needed and no obligation.</p></details>
<details><summary>What happens to my details?</summary><p>They're used only to prepare your sample and contact you about it. They are never sold or shared.</p></details>
{CTA}</div></section>

<section id="sample"><div class="wrap"><div class="formbox"><span class="eyebrow" style="display:block;text-align:center">Free sample</span><h2>Get your free sample ad</h2><p class="lead">Tell me about your clinic. A real person replies within 2 working days.</p>{form}</div></div></section>
<footer>© Clinic Ads UAE · Sample work shown is not client work · Your details are never sold or shared</footer>
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
                (time.strftime("%Y-%m-%d %H:%M", time.gmtime(time.time()+4*3600)), d["name"], d["clinic"], d["email"], d["phone"], d["emirate"], d["specialty"], d["goal"])); c.commit()
            return self.send(200, page(ok=True))
        self.send(404, "Not found", "text/plain")

if __name__ == "__main__":
    if not ADMIN_PASS: print("WARNING: set ADMIN_PASSWORD; admin view stays locked until you do.")
    db(); ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", 8080))), H).serve_forever()
