# Team onboarding — one GitHub App for everyone

This document is for **admins** adding a developer and for **developers** joining a repo that vendors `.repo_ai` as a submodule.

## Core rule: one App, not one App per person

| Correct | Incorrect |
|---------|-----------|
| One **team** GitHub App (e.g. `ai-codex-dan[bot]`) installed on the repos you need | Each developer registers **their own** GitHub App |
| Each machine gets a **copy** of the same local secrets in `.repo_ai/secrets/` | Secrets committed to git or invented per developer |
| New hires get **repo collaborator** access **and** secrets out-of-band | Expecting “add me to the repo” alone to enable bot/agent git |

`.repo_ai` is **shared infrastructure**. Consumers treat `.repo_ai/` as **read-only**; change it in the **[repo-ai](https://github.com/fishdan/repo-ai)** repository, then update the submodule pin in each consumer repo.

---

## What admins do

1. **GitHub repo access** — Add the person as a collaborator or org member on consumer repos (e.g. MakeALetter) with the usual read/write (or tighter) role.
2. **GitHub App installation** — Confirm the **existing** team App is still installed on those repos (GitHub → **Settings** → **Developer settings** → **GitHub Apps** → your App → **Install App** → repository list). You do **not** install a different App per teammate.
3. **Secrets handoff** — Securely send the **same** local bundle every bot user needs (never via git):
   - `.repo_ai/secrets/config.txt` (`GITHUB_APP_ID`, `GITHUB_INSTALLATION_ID`)
   - `.repo_ai/secrets/*.private-key.pem` (or whatever filename your setup uses)
   See [`secrets/README.md`](../secrets/README.md) for how those files are created the first time.
4. **Submodule** — After clone: `git submodule update --init --recursive` so `.repo_ai` is present.
5. **Point them here** — They follow [Developer setup](#developer-setup) below.

If the App must access a **new** repository, an **owner** updates the App installation’s repo list. That is an App-admin action, not something a new collaborator does on their own.

---

## Developer setup

1. Clone the consumer repo and init submodules:
   ```bash
   git submodule update --init --recursive
   ```
2. Place secrets under `.repo_ai/secrets/` (from your admin; see `secrets/README.md`).
3. From the **consumer repo root**, bootstrap:
   ```bash
   .repo_ai/scripts/github-app-setup-git-auth.sh
   ```
4. Verify bot identity:
   ```bash
   git config user.name    # should contain [bot]
   git config user.email   # should end with @users.noreply.github.com
   ```
5. For **HTTPS** remotes to `origin`, use the consumer’s wrapper (example: MakeALetter):
   ```bash
   ./scripts/git-with-github-app.sh fetch origin
   ```
   For **SSH** remotes, push/pull use your SSH key; the script still sets commit author to the bot. You still need a fresh installation token for **`gh`** and GitHub API calls.

**Do not** create your own GitHub App for this workflow unless the team explicitly decides to replace the team App and rotate all secrets.

---

## Human git vs bot git

| Goal | Approach |
|------|----------|
| Normal personal commits as yourself | Use your own git credentials; do not run bot bootstrap for those commits |
| Agent/automation commits as the bot | Bootstrap + bot `user.name` / `user.email`; push per `repo.ai` (HTTPS wrapper or SSH + API token rules) |

Project agents (e.g. Cursor following `repo.ai`) must use **only** the GitHub App path, not personal PATs or OAuth.

---

## Can we tell which human triggered the App?

**Mostly no at the GitHub API layer** for how `.repo_ai` works today.

- **Installation access tokens** (JWT → installation token) act as the **App**, not as an end user. REST/`gh` calls authenticated that way appear as the bot/App.
- **Commits** pushed with bot identity show **`{app-slug}[bot]`** as author, regardless of who ran the agent on a laptop.
- There is **no** built-in field in installation tokens like “on behalf of alice@example.com.”

**Partial signals** (useful for ops, not proof):

| Signal | What it might tell you |
|--------|-------------------------|
| **SSH push** | If `origin` is `git@github.com:...`, the **transport** may be tied to whoever owns the SSH key, while **commit author** can still be `[bot]`. Org audit logs (GitHub Enterprise) can correlate SSH activity with members. |
| **HTTPS push** via installation token | Wire auth is the App; harder to see which human ran the command. |
| **Audit log** (org/enterprise) | May show App installations, repo events, and member activity depending on plan and settings — not a per-commit “triggered by” field in the public API for installation tokens. |
| **Your own discipline** | PR description, `Co-authored-by:`, branch naming, `progress.ai` / ticket IDs in commit messages, CI `GITHUB_ACTOR` in Actions (different from local agent use). |

**User-to-server** OAuth tokens *do* carry user identity, but this stack **deliberately avoids** them (see `repo.ai` — no PATs, no OAuth, no human credentials for agent work).

If you need stronger attribution later, that is a **product/process** choice (e.g. require human-signed commits for merges, signed audit trail in CI, or a dedicated “impersonation” App per environment) — not something the default installation-token flow provides out of the box.

---

## Troubleshooting

| Symptom | Likely fix |
|---------|------------|
| Bootstrap fails / empty repo list | Stale token: rerun `scripts/github-app-setup-git-auth.sh`; verify `GITHUB_INSTALLATION_ID` in `config.txt` matches the App installation in GitHub. |
| “Permission denied” on push (SSH) | Your **human** SSH key needs repo access; App secrets do not replace SSH for `git@github.com` remotes. |
| Auth prompt on `git push` (HTTPS) | Use the consumer’s `git-with-github-app.sh` wrapper; bare `git push` will hang or fail without a TTY. |
| Agent commits as your name | Bot git config not applied — fix bootstrap before pushing. |

Full bootstrap steps: [`repo.ai`](../repo.ai). Secret creation: [`secrets/README.md`](../secrets/README.md).
