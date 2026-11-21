# Web targets and terminal labs

The project has 37 challenges. Player-facing challenge names, descriptions and
URLs are neutral; the original manifest slugs remain stable for database updates
and old bookmarks. Public pages use `case-<database-id>` aliases. Existing
accounts, solves, points and hint history stay attached to the same challenge IDs.

## Update an existing installation

Stop the backend, replace the source files with the contents of this archive,
then restart. Keep your existing `.env` and `instance/` database. Rebuild the React
frontend for a deployed installation. The Flask factory automatically applies
the updated manifests on startup. No database migration or new runtime dependency
is required. A restart clears the in-process lab runtimes as before.

The update changes files across `app/labs/`, `app/core/routes.py`, `app/models.py`,
`app/templates/`, `challenges/` and `frontend/src/`. Copy the complete source tree
rather than only the challenge YAML files.

Fresh local setup:

```bash
cd myctf
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run.py
```

For React, in a second terminal:

```bash
cd myctf/frontend
npm install
npm run dev
```

Use the local URL printed by Vite. The Flask-rendered interface is also available
at http://127.0.0.1:8000 and has Target page / Terminal controls for hybrid labs.

## Player experience

Open a challenge and click Start lab. Web applications open on Target page when
browsing is the natural starting point. Protocol-focused exercises start in
Terminal. Hybrid labs provide both views without resetting their instance.

- **Target page:** interactive forms, navigation and the simulated application.
- **Source:** the exact target response body, including HTML comments.
- **Headers:** the HTTP status and server response headers.
- **Edit request:** choose a method, add headers and send a request body.
- **Terminal:** the existing command history, virtual filesystem and scenario tools.

Changing a cart or application state in one interface is visible in the other.
Browser-target login cookies and credentials stay within that lab instance and
never replace the platform authentication cookie. Restart creates a fresh flag
and clears browser authentication, virtual downloads and all target state.

## Browser interfaces

16 EWPT HTTP targets have web interfaces: cases 101–109, 111, 113–116, 119 and
120. Their player-facing names do not identify the technology or vulnerability.
For maintainers, these include:

- A Tomcat-style landing page, sign-in prompt, application manager and server status.
- Login portals and authenticated dashboards.
- A store with quantity, coupon and checkout forms.
- Company pages with source-level evidence.
- Swagger-style API documentation with an executable header parameter.
- A multi-step password reset and login flow.
- Default Apache/nginx-style pages, file listings and a product catalog.

Tomcat start, stop and reload controls update the virtual application state.
WAR deployment is explicitly disabled; nothing is uploaded or executed on the
host. The sign-in prompt reproduces the authentication flow inside the training
page instead of opening a native browser authentication dialog.

Technology banners and version numbers appear in target pages, headers or scans
where a learner would discover them. Pre-solve challenge metadata does not give
the player internal engine names or the original descriptive manifest slugs.
Optional hints remain opt-in; technical debriefs unlock after solving.

## Terminal tools

Type `help` for commands installed in the current lab. Existing shell built-ins
and pipes remain available. Each command runs individually; shell redirection,
`;`, `&&` and command substitution are unsupported.

HTTP targets support `curl` with `-i`, `-I`, `-X`, `-H`, `-d`, `--data`,
`--data-raw`, `--data-binary`, `--data-urlencode`, `--json`, `-u`, `--digest`,
`-b`, `-c`, `-o`, `-O` and `--path-as-is`. Form and JSON requests work. Downloads
are relative to the terminal's current directory. Cookie jars use a simplified
virtual format, separate from browser-target authentication state.

`ffuf` reads virtual wordlists and evaluates candidate requests against the same
target used by the web interface. Supported options: `-u`, `-w`, `-X`, `-d`, `-H`,
`-mc`, `-fc`, `-fs`, `-ms`. There is one `FUZZ` keyword and a cap of 256 wordlist
entries per invocation.

Labs that ship a word list (`wordlist.txt` or `api-wordlist.txt`) also provide
`gobuster dir -u URL -w LIST` (`-s`, `-b` status filters) and `dirb URL LIST`, with
the same 256-entry cap. They are not mentioned in hints or descriptions.

`chmod` accepts numeric (`600`) and symbolic (`+x`, `go-rwx`) modes; `ssh -i` refuses a
key that group/other can read. The key check ignores whitespace, so a key pasted with
`echo "..." > id_rsa` works. The shell supports one trailing `>` / `>>` redirect.

Relevant scenarios also provide `dig`, `nmap`, `ssh`, `chmod`, `xfreerdp`, `unzip`,
`awk`, `sort`, `uniq` or an `answer` reporting command. Discovery evidence is
inside each assigned environment. The log-analysis awk implementation supports
`awk '{print $1}'`; numeric/reverse sort and `uniq -c` work with pipes.

The browser request editor accepts up to 32 headers, a 2048-character path and
an 8192-character body. Requests stay on the assigned target. Old `.lab.local`
host aliases remain accepted by terminal tools for compatibility with old notes;
the player-facing scope is neutral.

## Simulation and isolation

No player command starts a process, reads the server filesystem or contacts an
external service. SQL teaching targets query a throwaway in-memory SQLite DB
containing only synthetic scenario data, never the platform DB.

Rendered target documents run in an iframe with an opaque origin. The sandbox
allows only the trusted form/navigation bridge; target documents cannot read
platform cookies, access the parent DOM or connect to external services. Source
and headers are displayed as text. Every request still passes lab ownership and
expiry checks.

SSH authenticates using a virtual key and mounts a simulated remote home. RDP
mounts desktop files after authentication; it does not render a desktop. Virtual
archives are understood by the terminal's unzip and are not binary ZIP files.
Digest authentication models the curl credential flow rather than implementing
a cryptographic Digest handshake. Service enumeration returns scenario data.

## Verification

```bash
python -m pytest
cd frontend
npm run build
```

The Python suite tests intended exploits and scoring, browser authentication,
shared terminal/browser state, hidden-source evidence, scope restrictions,
neutral public metadata, ownership and fresh state after reset. The frontend
build runs TypeScript validation. DOM integration was also checked against the
Flask endpoints for Tomcat, shopping, API docs and password reset.

Design references for the training reproductions:

- https://tomcat.apache.org/tomcat-8.5-doc/html-manager-howto.html
- https://fastapi.tiangolo.com/tutorial/first-steps/
