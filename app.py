import re
import streamlit as st
import streamlit.components.v1 as components
from anthropic import Anthropic
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Activator — Pre-Program Diagnostic",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── URL parameter guard ────────────────────────────────────────────────────────
_params = st.query_params
ORG_NAME = _params.get("org", "").strip()
if not ORG_NAME:
    st.error(
        "This link appears to be incomplete. "
        "Please contact Tien-Ti for the correct link.",
        icon="🔗",
    )
    st.stop()


# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    #MainMenu, footer, header { visibility: hidden; }
    .stApp { background-color: #f7f9fc; }
    .diagnostic-header {
        background: linear-gradient(135deg, #0E2841 0%, #156082 100%);
        color: white;
        padding: 22px 28px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .diagnostic-header h2 {
        color: white;
        font-size: 20px;
        margin: 0 0 4px 0;
        font-weight: 700;
        letter-spacing: 0.3px;
    }
    .diagnostic-header p {
        color: #9BBFD8;
        font-size: 12.5px;
        margin: 0;
    }
    .summary-header {
        background: #0F9ED5;
        color: white;
        padding: 10px 16px;
        border-radius: 8px 8px 0 0;
        font-weight: 600;
        font-size: 13px;
    }
    .summary-body {
        background: #F0F5FA;
        border: 1px solid #C8D8E8;
        border-top: none;
        border-radius: 0 0 8px 8px;
        padding: 16px;
        font-family: 'Courier New', monospace;
        font-size: 11.5px;
        white-space: pre-wrap;
        line-height: 1.6;
        color: #1a2e42;
    }
    .complete-notice {
        background: #E8F4F0;
        border: 1px solid #4CAF7D;
        border-radius: 8px;
        padding: 14px 18px;
        font-size: 13px;
        color: #1a4a30;
        margin-top: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ── System prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a warm, professional pre-session diagnostic assistant created by
Tien-Ti Mak (he/him) to help him prepare for a Claude training session
with the Pemba Capital Partners team. Your job is to have a genuine,
one-on-one conversation with each participant — not to administer a form.
Tien-Ti will personally read every summary you produce.

## Your character
- Genuinely curious and interested in what participants share
- Warm and human — use natural language, not corporate speak
- Never sycophantic — never say "Great answer!", "Wonderful!",
  "That's fascinating!" or similar filler praise
- Non-judgmental — especially about low AI usage or anxiety
- Ask ONE question at a time. Never combine two questions in a single turn
- Keep your responses concise — this is a conversation, not a presentation
- Use the participant's name naturally where it flows (if they've shared it),
  but not in every single turn

## Context you need
Pemba Capital Partners ran a full AI Super Week in February 2026 — a
5-day immersive program built around ChatGPT Business. The team has a
solid AI foundation. This diagnostic is specifically designed to understand
where they've landed since then and to shape a focused 2-hour Claude
session. Participants know AI; you don't need to explain basics or be
encouraging about getting started — they already have.

## Conversation flow
Work through the five questions below in order. Transition naturally between
them — don't announce question numbers. Probe interesting answers before
moving on, but don't interrogate — one follow-up per question is enough.

### OPENING
Introduce yourself briefly and warmly. Explain that:
- Tien-Ti asked you to have this conversation before the Claude session
- He'll read every response personally
- There are no right or wrong answers
- They can skip any question by saying "skip" or "pass" — no explanation needed
- The conversation takes about 5–10 minutes

Ask for their first name to get started — but note it's optional if they'd
prefer to stay anonymous.

### QUESTION 1 — AI usage since Super Week
Ask: "Since AI Super Week in February, how has your day-to-day use of AI
tools changed — if at all?"

Probes (use one if warranted):
- If usage has grown: "What's driven that — any particular tools or tasks
  that clicked?"
- If usage has faded or stayed flat: "What's got in the way?"
  (non-judgmental — this is useful signal, not a failure)
- If they mention a specific workflow, note it for the summary

### QUESTION 2 — ChatGPT highlights and frustrations
Ask: "What's the most useful thing you've done with ChatGPT?"

When they've answered, follow up naturally: "And where has it let you down
or frustrated you?" — treat this as the second half of the same topic,
not a new question.

Probes:
- On highlights: "What made that work well — was it the task type, how
  you prompted it, something else?"
- On frustrations: let them expand if they want; don't push if they have none

### QUESTION 3 — Claude experience
Ask: "Have you tried Claude yet? If so, what for — and what did you notice?"

Branching:
- If YES: follow up with "What stood out compared to ChatGPT?" then move on
- If NO: ask "What's made you curious about it?" — or if they seem
  indifferent: "What would make it worth your time to try?"

### QUESTION 4 — Still-manual tasks
Ask: "What's one task in your Pemba work that still feels more manual
than it should be?"

Probe (only if they give a specific task): "Roughly how often does that
come up in your week?"

### QUESTION 5 — Session goals
Ask: "Is there anything specific you're hoping to get out of this session?"

No probe needed — just listen. If their answer is very vague
("learn more about Claude"), you can gently ask: "Is there a particular
task or problem you'd love to leave the session having made progress on?"

### CLOSING
Thank them warmly and genuinely — with a specific acknowledgement of
something they shared, not hollow praise. Let them know Tien-Ti will
review their responses before the session.

## Handling skips and anonymity
If a participant says "skip", "pass", "rather not" or similar, respond
with "No problem at all." and move to the next question. Note every skip
in the summary. Never ask why.
If they prefer to stay anonymous, note this clearly in the summary.

## Structured summary
When the conversation is complete, produce the summary in EXACTLY this
format. The summary is for Tien-Ti's eyes only and will arrive via email.

---SUMMARY---
PEMBA — CLAUDE SESSION PRE-DIAGNOSTIC
Organisation: Pemba Capital Partners
Participant: [first name, or "Anonymous"]
Date: [date]

1. AI USAGE SINCE SUPER WEEK:
[2–3 sentences. Note trajectory: growing, stable, or faded — and what's
driven it either way.]

2. CHATGPT HIGHLIGHTS & FRUSTRATIONS:
Highlight: [specific example, or "Not shared"]
Frustration: [specific example, or "None raised"]

3. CLAUDE EXPERIENCE:
[What they've used it for and what they noticed, or "Not yet tried —
[their stated reason or curiosity]"]

4. MOST MANUAL TASK:
[Description + rough frequency if mentioned, or "Not shared"]

5. SESSION GOALS:
[Their own words where possible]

FLAGS FOR TIEN-TI:
[Notable signals: strong Claude user already, usage has faded since
Super Week, specific session request, interesting use case, anything
worth addressing directly in the session. If none: "None."]

QUESTIONS SKIPPED: [list, or "None"]
---END SUMMARY---
"""

# ── Helpers ────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_client():
    return Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])


def get_response(messages: list, org_name: str = "") -> str:
    client = get_client()
    system = SYSTEM_PROMPT.replace("{ORG_NAME}", org_name) if org_name else SYSTEM_PROMPT
    result = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=[
            {
                "type": "text",
                "text": system,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=messages
    )
    return result.content[0].text


def extract_summary(text: str) -> str | None:
    if "---SUMMARY---" in text and "---END SUMMARY---" in text:
        start = text.index("---SUMMARY---") + len("---SUMMARY---")
        end   = text.index("---END SUMMARY---")
        return text[start:end].strip()
    return None


def visible_text(text: str) -> str:
    if "---SUMMARY---" in text:
        return text[:text.index("---SUMMARY---")].strip()
    return text


TRIGGER = "__BEGIN__"


# ── Email ──────────────────────────────────────────────────────────────────────
def send_summary_email(summary: str) -> bool:
    try:
        sender    = st.secrets["EMAIL_SENDER"]
        password  = st.secrets["EMAIL_PASSWORD"]
        recipient = st.secrets["EMAIL_RECIPIENT"]

        timestamp = datetime.now().strftime("%d %b %Y  %H:%M")
        subject   = f"AI Activator — Pre-Program Diagnostic  ·  {ORG_NAME}  ·  {timestamp}"

        msg = MIMEMultipart()
        msg["From"]    = sender
        msg["To"]      = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(summary, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        return True

    except Exception:
        return False


# ── Session state init ─────────────────────────────────────────────────────────
if "messages"         not in st.session_state:
    st.session_state.messages         = []
if "summary"          not in st.session_state:
    st.session_state.summary          = None
if "complete"         not in st.session_state:
    st.session_state.complete         = False
if "pending_response" not in st.session_state:
    st.session_state.pending_response = False

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="diagnostic-header">
    <h2>AI Activator &mdash; Pre-Program Diagnostic</h2>
    <p>A private conversation to help Tien-Ti personalise your program &nbsp;·&nbsp; Approx. 5&ndash;10 minutes &nbsp;·&nbsp; You can skip any question</p>
    <div style="display:inline-block;background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.25);
                color:white;padding:0.25rem 0.9rem;border-radius:20px;font-size:0.85rem;margin-top:0.6rem;">
        📋 {ORG_NAME}
    </div>
</div>
""", unsafe_allow_html=True)

# ── Start button ───────────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown(
        "<p style='text-align:center; color:#666; margin: 1rem 0 1.5rem;'>"
        "This private conversation takes about 5–10 minutes. "
        "You can skip any question at any time.</p>",
        unsafe_allow_html=True
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Begin →", type="primary", use_container_width=True):
            with st.spinner(""):
                opening = get_response([{"role": "user", "content": TRIGGER}], ORG_NAME)
            st.session_state.messages = [
                {"role": "user",      "content": TRIGGER},
                {"role": "assistant", "content": opening},
            ]
            st.rerun()

# ── Render conversation ────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    if msg["content"] == TRIGGER:
        continue
    role    = msg["role"]
    display = visible_text(msg["content"])
    if not display:
        continue
    avatar = "💬" if role == "assistant" else "👤"
    with st.chat_message(role, avatar=avatar):
        st.write(display)

# ── Summary panel ──────────────────────────────────────────────────────────────
if st.session_state.summary:
    if not st.session_state.get("email_sent"):
        st.session_state.email_sent = send_summary_email(st.session_state.summary)

    st.markdown("---")
    st.markdown("""
    <div class="complete-notice">
    ✅ &nbsp;<strong>You're all done — and your responses have been sent to Tien-Ti automatically.</strong>
    He'll review them before the session and may drop you a quick note if he has any follow-up questions.
    Thanks for taking the time.
    </div>
    """, unsafe_allow_html=True)
    st.markdown("")

    with st.expander("Want to keep a copy of your responses?"):
        filename = f"Pemba_Claude_PreDiagnostic_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        st.download_button(
            label="⬇️  Download a copy",
            data=st.session_state.summary,
            file_name=filename,
            mime="text/plain",
        )
        st.caption(
            "Your summary has already been shared with Tien-Ti. "
            "This download is just for your own reference."
        )

    if not st.session_state.get("email_sent"):
        contact_email = st.secrets.get("EMAIL_RECIPIENT", "")
        contact_str = f" at {contact_email}" if contact_email else ""
        st.warning(
            f"Something went wrong sending your results automatically. "
            f"Please contact Tien-Ti{contact_str} to let him know.",
            icon="⚠️"
        )

# ── Chat input ─────────────────────────────────────────────────────────────────
if not st.session_state.complete:
    if st.session_state.pending_response:
        st.session_state.pending_response = False
        with st.spinner(""):
            reply = get_response(st.session_state.messages, ORG_NAME)
        summary = extract_summary(reply)
        if summary:
            _ts = datetime.now().strftime("%d %b %Y  %H:%M")
            summary = re.sub(r"Date:.*", f"Date: {_ts}", summary)
            st.session_state.summary  = summary
            st.session_state.complete = True
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

    if user_input := st.chat_input("Type your response here…"):
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.pending_response = True
        st.rerun()
else:
    st.info("This conversation is complete. Thank you for your time!", icon="✅")

# ── Auto-scroll ────────────────────────────────────────────────────────────────
if st.session_state.complete and not st.session_state.get("scrolled_to_bottom"):
    components.html("""
    <script>
        var el = window.parent.document.querySelector('section[data-testid="stMain"]');
        if (!el) el = window.parent.document.querySelector('.main');
        if (el) el.scrollTop = el.scrollHeight;
    </script>
    """, height=0)
    st.session_state.scrolled_to_bottom = True
