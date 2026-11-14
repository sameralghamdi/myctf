# Deploying MyCTF (Cloudflare Pages + Flask on a VPS)

```
 Browser ──HTTPS──▶  yourdomain.com  (Cloudflare Pages)
                         │  static React app  (frontend/dist)
                         │
                         └─ /api/*  /admin/api/*  /labs/*
                               │   Pages Function (frontend/functions)
                               │   adds X-Origin-Secret + real client IP
                               ▼
                        api.yourdomain.com  (Cloudflare Tunnel, outbound only)
                               ▼
                        VPS:  cloudflared ─▶ gunicorn + Flask + SQLite
```

Why this shape: the browser only talks to **one origin** (your domain), so the login
cookie is first-party (no CORS, no cross-site cookie problems). The VPS opens **no
inbound ports** and only accepts requests that carry the shared secret.

> Cloudflare's dashboard labels change from time to time. If a menu name below does not
> match what you see, search the Cloudflare docs for the term in **bold**.

## 0. What you need

- A domain **added to Cloudflare** (Cloudflare account → Add a site → change the domain's
  nameservers at your registrar to the two Cloudflare gives you).
- A GitHub account (Cloudflare Pages builds from a repo).
- A VPS: Ubuntu 22.04+, 1 vCPU / 1 GB RAM is enough to start.

### Where does the backend go?

The Flask API cannot run on Cloudflare Pages (Pages only hosts static files and tiny
functions), and it keeps lab state and a SQLite database in memory/on disk, so it needs
**one small always-on Linux server (a VPS)**. Any provider works; pick one in a region
close to your users: Hetzner, DigitalOcean, Vultr, Linode/Akamai, OVH, Contabo or AWS
Lightsail. Choose **Ubuntu 24.04 LTS**, **1–2 vCPU, 2 GB RAM** (1 GB works for a small
class), 20 GB disk, and add your **SSH key** when creating it (no password logins).

Your own PC also works for a demo: run the same `docker compose` there; the Cloudflare
Tunnel exposes it without opening any router port. The site is then only up while the PC is on.

First-time server hardening (5 minutes):

```bash
ssh root@SERVER_IP
adduser deploy && usermod -aG sudo deploy        # work as a normal user
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy
sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/; s/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart ssh
apt update && apt -y upgrade && apt -y install unattended-upgrades ufw
```

## 1. Put the code on GitHub

```bash
cd myctf
git add -A && git commit -m "MyCTF: React frontend + production setup"
# create an empty PRIVATE repo on GitHub, then:
git remote add origin git@github.com:YOU/myctf.git
git push -u origin main
```

`.env.prod` is never committed (see `.gitignore`); you create it on the server.

## 2. Backend on the VPS

```bash
# on the VPS
curl -fsSL https://get.docker.com | sh
git clone git@github.com:YOU/myctf.git && cd myctf
cp .env.prod.example .env.prod
```

Edit `.env.prod`:

| Variable | What to put |
|---|---|
| `MYCTF_SECRET_KEY` | `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `MYCTF_ADMIN_PASSWORD` | a strong password (12+ chars). The `admin` account is created on first start. |
| `MYCTF_ALLOWED_ORIGINS` | your site, exactly as typed in the browser: `https://yourdomain.com` (comma-separate extras such as `https://www.yourdomain.com`). Anything else cannot log in or change data. |
| `MYCTF_ORIGIN_SECRET` | `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` — **keep a copy**, you enter it in Pages too |
| `TUNNEL_TOKEN` | from the next step |

The server **refuses to start** if the secret key, admin password or origin secret are
still the defaults, if `MYCTF_COOKIE_SECURE` or `MYCTF_ALLOWED_ORIGINS` is missing, or if
`MYCTF_EXPOSE_DEV_LINKS` / `MYCTF_DEBUG` is on. Then protect the file:
`chmod 600 .env.prod`.

### Create the Cloudflare Tunnel

1. Cloudflare dashboard → **Zero Trust** → **Networks** → **Tunnels** → **Create a tunnel**
   → type **Cloudflared** → name it `myctf`.
2. On the "install connector" screen, copy the **token** (the long string after
   `--token` / `service install`). Put it in `.env.prod` as `TUNNEL_TOKEN`.
   You do **not** run the install command; Docker Compose runs `cloudflared` for you.
3. Add a **public hostname**: subdomain `api`, domain `yourdomain.com`,
   service type **HTTP**, URL `app:8000`.

### Start it

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
docker compose -f docker-compose.prod.yml logs -f      # Ctrl-C to leave
```

Check from your own computer:

```bash
curl https://api.yourdomain.com/healthz        # {"status":"ok"}
curl -i https://api.yourdomain.com/api/public   # 403 — correct: no secret, no entry
```

Lock the VPS down (nothing needs to be reachable except SSH):

```bash
sudo ufw default deny incoming && sudo ufw allow OpenSSH && sudo ufw enable
```

## 3. Frontend on Cloudflare Pages

1. Cloudflare dashboard → **Workers & Pages** → **Create** → **Pages** →
   **Connect to Git** → pick the repo.
2. Build settings:
   - **Framework preset:** None (or Vite)
   - **Root directory:** `frontend`
   - **Build command:** `npm run build`
   - **Build output directory:** `dist`
3. **Environment variables** (Settings → Variables and Secrets, Production):
   - `NODE_VERSION` = `20`
   - `ORIGIN_URL` = `https://api.yourdomain.com`
   - `ORIGIN_SECRET` = the same value as `MYCTF_ORIGIN_SECRET` (add as **Secret**)
4. **Save and Deploy.** In the build log you should see the Functions being picked up
   (`frontend/functions`). If it says no Functions were found, the **Root directory**
   is wrong: it must be the folder that contains both `package.json` and `functions/`.
5. **Custom domains** tab → **Set up a custom domain** → `yourdomain.com` (and `www`
   if you want it). Cloudflare creates the DNS records for you.

Visit `https://yourdomain.com`, register, and sign in. Sign in as `admin` with
`MYCTF_ADMIN_PASSWORD` to see the admin panel.

Every `git push` to `main` redeploys the frontend automatically. To update the backend:

```bash
cd myctf && git pull
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

## 4. Local development

```bash
# terminal 1 — API on :8000 (dev links on so the reset flow is testable)
MYCTF_EXPOSE_DEV_LINKS=1 python3 run.py

# terminal 2 — React on :5173, proxying /api, /admin/api and /labs to :8000
cd frontend && npm install && npm run dev
```

Open http://localhost:5173. The `admin` password is printed once in terminal 1 on the very first start
(or set `MYCTF_ADMIN_PASSWORD` before starting).

## 5. Things to know before going public

- **No email yet.** Password reset and email verification need a mailer. On a public
  site the reset link is (correctly) **not** returned by the API, so "forgot password"
  cannot complete until you add SMTP. An admin can't reset passwords from the UI either.
- **One worker, SQLite.** Lab state and rate limiting live in process memory, so the
  container runs one gunicorn worker with 8 threads. Restarting the container stops any
  running labs (users just click Start again). Don't raise `--workers` without moving
  that state to Redis/Postgres (see `docs/ARCHITECTURE.md`).
- **Back up the database.** It lives in the `myctf_instance` Docker volume:
  ```bash
  docker run --rm -v myctf_myctf_instance:/data -v "$PWD":/backup alpine \
    tar czf /backup/myctf-$(date +%F).tgz -C /data .
  ```
  (The volume is prefixed with the compose project name; check `docker volume ls`.)
- **Brute force.** Login is limited per account and per IP. For more protection, add a
  Cloudflare **WAF rate-limiting rule** on `/api/auth/*` and consider Turnstile on the
  register form.
- **Labs are simulations.** The vulnerable targets run in-process with no real shell or
  subprocess, so a successful "exploit" can't touch the server. They are still served from
  your main domain under `/labs/…`.
- **Rotate secrets** if they ever leak: change `MYCTF_SECRET_KEY` (signs sessions and flag
  hashes — this signs everyone out and **invalidates static flag hashes**, so only do it
  before launch) and `MYCTF_ORIGIN_SECRET` (update Pages too).

## 5a. Configuration files at a glance

| File | Where it lives | Contains | In git? |
|---|---|---|---|
| `.env.prod` (from `.env.prod.example`) | the VPS only | **all secrets**: secret key, admin password, origin secret, tunnel token | never |
| Pages **Variables and Secrets** (see `frontend/.dev.vars.example`) | Cloudflare dashboard | `ORIGIN_URL`, `ORIGIN_SECRET` (server-side, for the proxy function) | never |
| `frontend/.env` (from `frontend/.env.example`) | optional | public display settings only. `VITE_*` values end up in the public JavaScript. The app needs none. | never |

Three things that are deliberately **not** here, and why:

- **No CORS.** The browser only ever talks to your own domain; the Pages Function
  forwards API calls server-side. The API sends no `Access-Control-*` headers at all, so
  no other website can read from it, and every state-changing request must come from an
  origin in `MYCTF_ALLOWED_ORIGINS`. That is stricter than an allow-list CORS policy.
- **No PM2 / cluster mode.** The API runs under gunicorn inside Docker, and Docker
  restarts it if it crashes or the server reboots (`restart: unless-stopped`). It must
  stay at **one process**: running labs and rate-limit counters live in that process's
  memory, so a cluster would give each player a different, empty lab on every request.
- **No default admin password.** Production requires `MYCTF_ADMIN_PASSWORD`; locally a
  random one is printed once on first start.

Day-to-day commands on the server: `make prod-up` (start or update), `make prod-logs`,
`make prod-backup`.

## 5b. Security checklist

Built into the code (covered by `tests/test_security.py`):

| Area | Protection |
|---|---|
| Direct access | API only answers requests carrying the secret from the Cloudflare proxy; VPS publishes no ports |
| CSRF | `SameSite=Lax` cookie **plus** an `Origin` check on every POST/PUT/PATCH/DELETE (`MYCTF_ALLOWED_ORIGINS`) |
| Login | per-account and per-IP limits; 2FA codes locked after 5 wrong tries; constant-time check even for unknown usernames; password length capped |
| Sessions | HttpOnly + Secure cookie; server-side revocable; **a password reset signs out every session** |
| 2FA | turning it off needs password **and** a current code |
| Abuse | rate limits on register, forgot/reset password, flag submit, terminal commands; a global per-IP ceiling (`MYCTF_RL_GLOBAL`, default 1200/min); 1 MB request cap |
| Accounts | usernames are case-insensitively unique (no `Admin` look-alikes) |
| Content | draft (unpublished) challenges can't be played; manifests reject negative hint costs, bad URLs, huge points |
| Admin | can't demote themselves; every action audited |
| Headers | nosniff, DENY framing for the API, no-referrer, HSTS, `no-store` on API and labs |
| Container | non-root, read-only filesystem, all capabilities dropped, memory/CPU/process limits |

You still need to do (cannot be done in code):

1. In Cloudflare → **SSL/TLS**: mode **Full (strict)**; turn on **Always Use HTTPS** and
   **HSTS**.
2. Cloudflare → **Security → WAF → Rate limiting**: limit `/api/auth/*` (for example 20
   requests / minute / IP).
3. Cloudflare **Turnstile** on the register form once you open registration publicly.
4. Keep the server patched (`unattended-upgrades`, installed above) and rebuild the image
   now and then: `docker compose ... up -d --build`.
5. Run `pip install pip-audit && pip-audit -r requirements.txt` and `npm audit` in
   `frontend/` before each release.
6. Back up the volume (section 5) and test a restore once.
7. Never reuse the admin password anywhere else; enable 2FA on the admin account after
   first login.

Known limits you accept for now: lab pages are served from your own domain (only their
owner can open them, and they run no real code); there is no email, so there is no
"forgot password" on a public site yet; the SQLite file is a single point of failure.

## 6. Troubleshooting

| Symptom | Likely cause |
|---|---|
| Site loads, every API call is **502** "API is unreachable" | Tunnel not running, or `ORIGIN_URL` wrong. `docker compose ... logs cloudflared` |
| API calls return **403** | `ORIGIN_SECRET` in Pages ≠ `MYCTF_ORIGIN_SECRET` on the server |
| Login says **"Cross-site request blocked"** | `MYCTF_ALLOWED_ORIGINS` doesn't exactly match the address in the browser (check `https://`, `www.`, no trailing slash) |
| API calls return **500** "ORIGIN_URL is not configured" | Variable missing for the **Production** environment; redeploy after adding it |
| Login works, then you're signed out on refresh | `MYCTF_COOKIE_SECURE=1` while visiting over plain `http://` (local), or the domain is not on HTTPS |
| Blank page on build | Output directory must be `dist`; check the Node version is 20+ |
| `/challenges/xyz` 404s on refresh | A `404.html` exists in the build output; remove it so Pages uses SPA fallback |
| Container exits: "Refusing to start" | Read the listed problems; fix `.env.prod` |
