# PyGuide — Python Assistant

PyGuide is a small web workspace for learning and working with Python. It combines rule-based code feedback with an optional language-model provider, private saved projects, and an installable mobile-friendly interface.

The project is designed to make the tradeoffs visible: local checks run without sending code to a model provider, while model output can be more flexible but may be wrong. PyGuide does not execute submitted or generated code.

## Features

- **Five assistant actions:** generate an example, review source, suggest a narrow syntax fix, explain an error, and explain program logic.
- **Two generation paths:** a local keyword/example generator and an optional Ollama or OpenAI model provider.
- **Syntax feedback:** generated model code is checked with Python's parser. A successful parse says nothing about whether the program behaves correctly.
- **Accounts and persistence:** usernames, password hashes, projects, and snippets are stored in SQLite. Users can only read or delete their own projects and snippets.
- **Admin workspace:** review account roles and aggregate seven-day usage, and add, edit, enable, or remove examples used by the local generator. Admin analytics do not store prompts or source code.
- **Responsive client and PWA shell:** use the responsive browser UI on a phone, or install it where the browser offers installation. The cached shell does not make account or model APIs work offline.
- **JSON API:** the browser client uses authenticated Flask endpoints rather than form-posting source to template routes.
- **Model evaluation command:** compare the configured model with the local generator on the same fixed prompts using syntax and expected-function-name checks.

The main API routes are `GET /api/session`, `POST /api/register`, `POST /api/login`, `POST /api/logout`, `POST /api/assist`, `GET/POST /api/projects`, and project-scoped snippet routes under `/api/projects/<id>/snippets`. Admin routes are under `/api/admin/`. State-changing API requests require the session's CSRF header; the included browser client adds it automatically.

## Run on Windows

Install Python 3.10 or newer. From PowerShell:

```powershell
git clone https://github.com/HariomSThakur/python-code-assistant.git
cd python-code-assistant
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` before starting. For a local learning session, set a private admin username and password of at least 12 characters. `SECRET_KEY` is required in production; create a private random value of at least 32 characters, for example with `py -c "import secrets; print(secrets.token_hex(32))"`. Keep `.env` out of GitHub.

Start the development server:

```powershell
python app.py
```

Open <http://127.0.0.1:5000>. The development server binds to your own computer by default and debug mode is off. You can create a regular account in the app. The administrator account is created from `ADMIN_USERNAME` and `ADMIN_PASSWORD` when the SQLite database is initialized.

### Configure a language model (optional)

Without a configured provider, use the local rules and examples. The model toggle stays unavailable until a provider is configured.

**Ollama:** install and start Ollama on the same machine as PyGuide, download a model using Ollama, then set `AI_PROVIDER=ollama` and `OLLAMA_MODEL` in `.env`. `OLLAMA_BASE_URL` defaults to `http://127.0.0.1:11434`.

For local speed, `OLLAMA_KEEP_ALIVE=10m` keeps the model ready between requests (at the cost of keeping its memory in use), and `OLLAMA_NUM_PREDICT=1024` caps answer length. The token limit can be set from 128 to 2048; use a higher value when generated code is being cut short. Ollama unloads models after a period of inactivity by default, so the first request after unloading may take longer.

**OpenAI:** set `AI_PROVIDER=openai`, `OPENAI_MODEL`, and `OPENAI_API_KEY` in `.env`. The app sends requests to the Responses API. API use may incur charges under the configured account. Never put the key in JavaScript, a committed file, or a public screenshot.

The interface displays a notice before model use: when the toggle is on, the text entered for that action is sent to the configured provider. Avoid private source, credentials, personal data, or other sensitive content. Local mode sends no prompt to an external model provider.

To reduce accidental API spend, signed-in accounts are limited to 8 model requests per minute and 100 per day. These starter limits are enforced per account; they are not a substitute for provider-side spending controls.

## Use the workspace

1. Create an account or sign in.
2. Enter a small generation request or paste Python into the assistant box.
3. Pick an action. For **Explain logic**, choose the explanation level.
4. Leave **Use language model** off for local generation and rule-based analysis. Turn it on only after configuring a provider and deciding to share the entered text with that provider.
5. Read and review the result. PyGuide does not run it or guarantee correctness. The syntax status only reports whether Python can parse generated code.
6. Create a project under **My projects**, then save useful results there. Saved snippets are stored in SQLite until removed or the database is deleted.
7. Sign in with the configured admin account to manage user roles and local generator examples.

For mobile use, open the deployed HTTPS site in a supported browser and choose its **Install app** prompt. On iPhone/iPad, use Safari's Share menu and choose **Add to Home Screen**. Localhost is secure for development; a phone connecting to a computer's LAN address needs HTTPS for PWA installation.

## Admin setup and controls

On the first run, set both `ADMIN_USERNAME` and `ADMIN_PASSWORD` in `.env`; restart the app to initialize the database and create the administrator. Use a long, unique password. If an existing username matches, startup promotes it to admin without changing its password. Remove the bootstrap variables after the account is created if you do not want startup to promote that username again.

The admin page shows account/project/snippet counts and recent request counts by assistant action and mode. It does not display prompt contents, submitted source, or saved snippet text. Admins can edit example templates used by local generation and change user roles. Keep admin credentials private.

## Compare model outputs

After configuring a model, run this command from the repository root:

```powershell
python -m assistant.evaluate
```

It sends six fixed, generic coding prompts to the configured model and compares those results with the local generator. The report is written to `artifacts/model-evaluation.json`, which is ignored by Git. It contains aggregate counts, prompt IDs, syntax validity, expected function-name matches, provider/model names, and latency; it does not include prompt text or generated code.

This is a starter evaluation, not a benchmark of functional correctness. It does not execute generated code, validate edge-case behavior, measure security, or replace human review. Run it only if you are comfortable sending its prompts to the configured provider and (for a paid API) making those requests.

## Data and privacy notes

- SQLite is created under Flask's `instance/` folder by default. Set `DATABASE_PATH` to choose another path. Back up this file to preserve accounts and saved work.
- Passwords are stored as hashes, not as plain text.
- Usage records include account ID, action, provider/mode, input length, success, duration, and timestamp. They intentionally do not include prompt or source contents.
- Failed sign-in attempts retain the requester IP address and timestamp for rate limiting; successful login clears that IP's failures, and old records are pruned when a later sign-in occurs.
- Code is stored only when a user explicitly saves a result as a snippet. A saved snippet contains the generated assistant result, not an automatic copy of the original input.
- This project has no password reset or email verification flow. For a public service, add a production identity and account-recovery design before inviting users.

## Production notes

For a simple deployment, install the dependencies and run with Waitress:

```powershell
waitress-serve --host 0.0.0.0 --port 8080 --call assistant:create_app
```

Set `APP_ENV=production`, a private `SECRET_KEY`, and the database/admin/provider environment variables in the hosting platform's secret settings. Serve the site behind HTTPS. The PWA install prompt requires a secure context (HTTPS, or localhost during development).

The default database is a local SQLite file. On a cloud host, attach persistent storage to the `instance/` directory or set `DATABASE_PATH` to a persistent volume; otherwise a redeploy may erase account data. A local Ollama URL is reachable only from the app host, so a cloud deployment needs a model provider endpoint accessible from that host. This starter has not been hardened or load-tested for a public multi-tenant service.

## Evaluation tasks and current limitations

- The local generator matches curated examples and does not understand arbitrary prompts.
- Review and explanation use selected static rules and Python's AST; this is not a replacement for a linter, type checker, tests, sandbox, or professional review.
- The optional language model can produce incorrect or unsafe suggestions. No generated code is executed by the server.
- SQLite is suitable for a small demonstration. Larger deployments may need managed database migrations, stronger rate limiting, account recovery, backups, monitoring, and a dedicated authentication setup.
- The PWA caches the application shell only; account data, saved snippets, and assistant requests are not available offline.
- The evaluation command reports no measured score until it is run with a configured provider. Do not claim a model win without publishing the actual report and explaining the limited rubric.

## Repository layout

```text
python-code-assistant/
├── app.py                         # Local development entry point
├── assistant/
│   ├── __init__.py                # Flask application factory
│   ├── analysis.py                # Rule-based review, fixes, and explanations
│   ├── db.py                      # SQLite schema, seed data, and helpers
│   ├── evaluate.py                # Optional local-vs-model evaluation
│   ├── generation.py              # Curated local code examples
│   ├── llm.py                     # Ollama and OpenAI provider adapters
│   ├── routes.py                  # JSON API, auth, user, and admin routes
│   └── services.py                # Assistant action dispatcher
├── evals/
│   └── code_tasks.json            # Fixed evaluation prompts and rubric targets
├── static/
│   ├── app.js                     # Browser client
│   ├── icon.svg                   # App icon
│   ├── icon-192.png               # Install icon
│   ├── icon-512.png               # Install/maskable icon
│   ├── manifest.webmanifest       # Installable app metadata
│   ├── service-worker.js          # Static shell cache; no API caching
│   └── style.css                  # Responsive UI
├── templates/
│   └── index.html                 # App shell
├── .env.example                   # Safe configuration template
├── .gitignore
├── requirements.txt
└── README.md
```

## Resume description

After you have run the app and evaluation and can explain the design, a truthful starting bullet is:

> Built a Python coding assistant with Flask, SQLite, user-owned projects, admin-managed examples, and optional Ollama/OpenAI generation; compared local and model outputs on a fixed prompt set using syntax and function-name checks.

Add measured evaluation results only after running the command and reviewing what its checks mean.
