# GitHub Actions Setup (One-time)

Before the daily auto-commit workflow works, do these steps once:

## 1. Push the repo to GitHub

```bash
git init
git remote add origin https://github.com/darshit2308/DocFlow.git
git add -A
git commit -m "chore: init repo structure and tooling"
git push -u origin main
```

## 2. Add one repository secret

Go to: **Settings → Secrets and variables → Actions → New repository secret**

| Secret name | Value |
|-------------|-------|
| `GIT_EMAIL` | Your GitHub email (e.g. `darshit@example.com`) |

> `GITHUB_TOKEN` is automatic — no need to add it.

## 3. Enable Actions

Go to **Settings → Actions → General** → Allow all actions.

## 4. Verify the workflow

Go to **Actions → Daily Progress Commit → Run workflow** and trigger it manually once.
Watch it make a commit. After that, it runs automatically every day.

## 5. What happens automatically

- Every day, GitHub Actions runs `infra/auto_commit.py`
- The script figures out which project day it is (relative to Nov 25, 2026)
- It creates/updates real source files matching that day's planned milestone
- It commits with a meaningful conventional commit message
- Commits are scattered across morning / afternoon / evening IST

## 6. Manual override (if you want to run a specific day's work)

Go to **Actions → Daily Progress Commit → Run workflow** and enter a day number in the input field.

## 7. Authenticity notes

- The automation writes **real code stubs and documentation** — not empty files
- Commit times are randomized across different hours of the day
- Commit sizes vary (1–5 files) organically
- You can also commit manually on top of the auto-commits — that's encouraged
