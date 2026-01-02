```md
# Secrets Directory — GitHub App (Bot) Authentication

This directory contains **local-only secrets** required to authenticate as a **GitHub App bot**.

⚠️ **Nothing in this directory should ever be committed**, except this README and safe example files.
All real secrets must remain untracked and local.

---

## What This Is

This repository uses a **GitHub App** (not a human user) for authentication.

All git commits and pushes must:
- Authenticate **only** as the GitHub App
- Be authored as `{app-slug}[bot]`
- Use **installation access tokens**, never personal credentials

This directory holds the **private key and config** needed to generate those tokens.

---

## Files Expected Here (Uncommitted)

You are expected to create the following files locally:

```

secrets/
├── config.txt
└── <app-name>.private-key.pem

```

These files are **ignored by git** and must never be shared.

---

## Step 1: Create the GitHub App

1. Go to GitHub → **Settings** → **Developer settings**
2. Click **GitHub Apps**
3. Click **New GitHub App**

### Required settings

**App name**
- Example: `ai-codex-dan`
- This determines the bot name: `ai-codex-dan[bot]`

**Homepage URL**
- Any valid URL (e.g. your GitHub profile or repo)

**Webhook**
- ❌ Disable (unless you explicitly need it)

**Permissions**
- Repository permissions:
  - Contents: **Read & write**
  - Metadata: **Read**
- No admin permissions unless explicitly required

**Where can this GitHub App be installed?**
- Choose **Only on this account** (recommended)

Save the app once configured.

---

## Step 2: Generate and Download the Private Key

1. Open your newly created GitHub App
2. Scroll to **Private keys**
3. Click **Generate a private key**
4. Download the `.pem` file

Move it into this directory and rename if desired:

```

secrets/ai-codex-dan.private-key.pem

```

⚠️ Treat this file like a password.  
Anyone with it can act as the bot.

---

## Step 3: Install the App on Repositories

1. In the GitHub App settings, click **Install App**
2. Choose:
   - Your user or organization
   - The repositories this bot should access
3. Complete the installation

After installation, GitHub assigns an **Installation ID**.

---

## Step 4: Create `config.txt`

Create a file at:

```

secrets/config.txt

```

With the following contents:

```

APP_ID=<GitHub App ID>
INSTALLATION_ID=<GitHub Installation ID>

```

Where:
- **APP_ID** is shown on the GitHub App settings page
- **INSTALLATION_ID** can be found:
  - In the installation URL, or
  - Via the GitHub API if needed

Example:

```

APP_ID=2461425
INSTALLATION_ID=51234567

```

---

## Step 5: Verify Git Ignore Rules

Ensure `.gitignore` includes at least:

```

secrets/*.pem
secrets/*.key
secrets/config.txt
secrets/*.private*
secrets/*.secret*

````

Run:

```bash
git status
````

You should **not** see any secrets listed.

---

## How These Secrets Are Used

* The private key is used **only** to generate a short-lived JWT
* The JWT is exchanged for a **1-hour installation access token**
* The installation token is used for:

  * `git push`
  * API validation
* Tokens are stored **only in memory or /tmp**, never committed

At no point are:

* Personal access tokens
* OAuth tokens
* Human credentials
  used or allowed.

---

## If Something Goes Wrong

If authentication fails:

* **Do not fall back to human credentials**
* **Do not commit as yourself**
* Fix the GitHub App configuration or secrets instead

This repository assumes **bot-only operation**.

---

## Summary

* This directory is **local-only**
* Secrets never leave your machine
* GitHub App == identity
* Bot commits only
* If in doubt: stop and fix auth, don’t bypass it

```

---