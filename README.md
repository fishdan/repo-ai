# repo-ai

**Shared repository automation and GitHub App (bot) infrastructure**

repo-ai is a reusable, versioned bundle of files that standardizes how repositories:

- authenticate as a **GitHub App**
- perform **bot-authored commits**
- manage short-lived installation tokens
- expose a consistent `repo.ai` entrypoint

It is designed to be included in other repositories as a **git submodule**.


---

## What This Repo Is

This repository provides **shared, security-critical infrastructure** for repositories that must:

- Authenticate **only** as a GitHub App (never as a human)
- Author commits as `{app-slug}[bot]`
- Avoid personal access tokens and OAuth
- Keep secrets local and uncommitted
- Use short-lived, auditable credentials

It is intentionally **opinionated** and **minimal**.

---

## What This Repo Is NOT

- ❌ An application
- ❌ A CI workflow collection
- ❌ A secrets store
- ❌ A place for repo-specific scripts
- ❌ A general utilities dumping ground

If something is project-specific, it does **not** belong here.

---

## How to Use

You work with your agent conversationally, while the repository provides shared context and guardrails.

A typical workflow looks like this:

**You:**
> Hey buddy — read the instructions in `.repo_ai` and remember them.

*(The agent loads and follows the shared `repo.ai` instructions.)*

*A few minutes later…*

**You:**
> Hey buddy, make a new branch called `foobar` and let’s start working there.

*(The agent creates the branch and begins work.)*

*A few hours later…*

**You:**
> Hey buddy — let’s commit everything, push it to our branch, and open a PR.

*(The agent commits as the bot, pushes using GitHub App authentication, and prepares a pull request.)*

That’s it.

The key idea is that **`.repo_ai` establishes shared rules and behavior**, so you don’t need to repeat setup, authentication, or workflow instructions in every conversation or repository.

Once the agent has read `.repo_ai`, you can just work.

---

## Repository Structure

```

repo-ai/
├── repo.ai                 # Canonical entrypoint for tooling
├── scripts/           # Shared executable scripts
│   ├── github-app-setup-git-auth.sh
│   ├── github-app-generate-jwt.py
│   └── github-app-get-installation-token.py
├── secrets/
│   ├── README.md           # How to create local GitHub App secrets
│   └── config.example.txt  # Safe placeholder (never real values)
├── .gitignore
└── README.md

````

All paths are **self-contained** and assume this repo lives at `.repo_ai/` when vendored.

---

## How This Repo Is Consumed

`repo-ai` is intended to be added to other repositories as a **git submodule**:

```bash
git submodule add https://github.com/<OWNER>/repo-ai.git .repo_ai
````

After cloning a repo that uses it:

```bash
git submodule update --init --recursive
```

Consumers should treat `.repo_ai/` as **read-only**.

All changes must be made in this repo and then pulled via submodule updates.

---

## Authentication Model (High Level)

* A **GitHub App** is the sole identity
* A private key is used locally to generate a short-lived JWT
* The JWT is exchanged for a **1-hour installation token**
* Git uses the installation token via `GIT_ASKPASS`
* Commits are authored as `{app-slug}[bot]`
* Tokens are never committed or logged

See `secrets/README.md` for setup details.

---

## Security Guarantees

This repo enforces the following invariants:

* No personal access tokens
* No OAuth tokens
* No human credentials
* No committed secrets
* No long-lived tokens
* No embedded credentials in git remotes

If authentication fails, the correct action is to **stop**, not to fall back.

---

## Versioning and Updates

* Each consuming repo pins a specific commit of `repo-ai`
* Updates are intentional and explicit
* Breaking changes should be rare and documented

This repo favors **stability over novelty**.

---

## License

This project is licensed under the **MIT License**.

You are free to use, modify, and redistribute it, provided that the license and copyright
notice are preserved.

See [`LICENSE`](./LICENSE) for full details.

---

## Contributing

Contributions are welcome **if and only if** they:

* Preserve the security model
* Avoid repo-specific assumptions
* Keep the surface area small
* Improve clarity or correctness

This repo values **boring, predictable correctness** over flexibility.

---

## Final Note

This repository exists to make the *right thing* the *easy thing* across many repos.

If you find yourself wanting to bypass it, that’s usually a sign something upstream
should be fixed instead.

```

---
