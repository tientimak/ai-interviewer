# AI Activator — Pre-Program Diagnostic

A conversational AI diagnostic tool that interviews participants before an AI Activator program. Built with Streamlit + Claude.

---

## What it does

- Conducts a 15–20 minute guided conversation with each participant
- Covers: their role and day-to-day work, current AI usage, blockers and concerns, hopes and expectations
- Adapts intelligently based on responses (e.g. branches differently for AI novices vs power users)
- Generates a structured one-page brief for Tien-Ti at the end of each conversation
- Participants can skip any question or stay anonymous

---

## Setup (one-time)

### 1. Get an Anthropic API key
Sign up at [console.anthropic.com](https://console.anthropic.com) if you don't have one.

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up automatic email delivery
The app emails the structured summary to Tien-Ti automatically the moment each conversation ends — participants do nothing. It uses Gmail's SMTP with an App Password (more secure than your main password).

**One-time Gmail setup:**
1. Sign into a Gmail account you want to use as the sender (recommended: create a dedicated one, e.g. `aiactivator.notify@gmail.com`)
2. Go to **Google Account → Security → 2-Step Verification** and enable it (required for App Passwords)
3. Go to **Google Account → Security → App Passwords**
4. Create a new App Password — name it "AI Activator" — copy the 16-character password shown

### 4. Set your secrets for local use
Create a file at `.streamlit/secrets.toml` (this file is gitignored — never commit it):
```toml
ANTHROPIC_API_KEY  = "sk-ant-..."
EMAIL_SENDER       = "aiactivator.notify@gmail.com"
EMAIL_PASSWORD     = "xxxx xxxx xxxx xxxx"   # the 16-char Gmail App Password
EMAIL_RECIPIENT    = "tientimak@live.com"    # optional — defaults to this if omitted
```

### 4. Run locally
```bash
streamlit run app.py
```
The app opens at `http://localhost:8501`

---

## Deploying a shareable link (Streamlit Community Cloud)

This is the recommended way to share with PortCo participants — free and takes about 5 minutes.

1. Push this folder to a GitHub repository (public or private)
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **New app** → select your repo and `app.py`
4. Under **Advanced settings → Secrets**, add all four secrets:
   ```
   ANTHROPIC_API_KEY  = "sk-ant-..."
   EMAIL_SENDER       = "aiactivator.notify@gmail.com"
   EMAIL_PASSWORD     = "xxxx xxxx xxxx xxxx"
   EMAIL_RECIPIENT    = "tientimak@live.com"
   ```
5. Click **Deploy** — you'll get a shareable URL like `https://yourapp.streamlit.app`

Send that URL to participants. Each person gets their own fresh conversation session.

---

## Collecting summaries

Summaries are delivered automatically — participants do nothing. The moment a conversation ends, the app emails the structured brief directly to Tien-Ti. The participant just sees a "You're all done" confirmation.

Participants are also offered an optional download so they can keep their own copy — but this is entirely their choice and has no effect on delivery.

If the automatic email fails for any reason (network issue, etc.), the app shows a fallback warning prompting the participant to download and send manually. This is a rare edge case.

> **On anonymity:** because the email is sent server-side, participants who choose to remain anonymous can do so freely — their name simply won't appear in the summary, but the summary still reaches Tien-Ti automatically.

---

## Customising the diagnostic

### Updating questions or tone
Edit the `SYSTEM_PROMPT` string in `app.py`. The prompt is written in plain English — no coding knowledge required to modify the questions, add new ones, or adjust the tone.

### Building the post-program version
Duplicate `app.py` as `app_post.py`. In the system prompt:
- Change the opening to reference the pre-program conversation: *"When we spoke before the program, you mentioned..."* (you'll need to pass in the pre-program summary as context)
- Replace the confidence score question with the same scale question (for comparison)
- Add the post-program questions: what's changed, what they're doing differently, NPS
- Update the summary format to include comparison fields

### Changing the email recipient
Search for `tientimak@live.com` in `app.py` and update it.

---

## Files

```
app.py                   ← Main application (edit this to change questions/behaviour)
requirements.txt         ← Python dependencies
.streamlit/
  config.toml            ← Theme (AI Activator colour scheme)
  secrets.toml           ← API key — LOCAL USE ONLY, never commit this file
README.md                ← This file
```

---

## Cost estimate

Each conversation uses approximately 3,000–5,000 tokens (input + output) with claude-sonnet-4-6.
At current Anthropic pricing, a cohort of 20 participants costs less than $1 in API usage.
