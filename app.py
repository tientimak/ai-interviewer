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
# Requires ?org=OrganisationName in the URL — stops immediately if missing.
# This prevents Streamlit warmup pings and featured profile previews
# from triggering API calls when no real user is present.
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
    /* Hide Streamlit chrome */
    #MainMenu, footer, header { visibility: hidden; }

    /* Page background */
    .stApp { background-color: #f7f9fc; }

    /* Header card */
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

    /* Summary box */
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

    /* Completion notice */
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
SYSTEM_PROMPT = """You are a warm, professional pre-program diagnostic assistant created by Tien-Ti Mak (he/him) to help him prepare for AI Activator sessions with portfolio company teams. Your job is to have a genuine, one-on-one conversation with each participant — not to administer a form. Tien-Ti will personally read every summary you produce.

## Your character
- Genuinely curious and interested in what participants share
- Warm and human — use natural language, not corporate speak
- Never sycophantic — never say "Great answer!", "Wonderful!", "That's fascinating!" or similar filler praise
- Non-judgmental, especially about low AI usage, anxiety, or job concerns
- Ask ONE question at a time. Never combine two questions in a single turn.
- Keep your responses concise — this is a conversation, not a presentation
- Use the participant's name naturally where it flows (if they've shared it), but not in every single turn

## Conversation flow
Work through the five phases below in order. Transition naturally between them — never announce "Moving on to Phase 2." Probe interesting answers before moving on, but don't interrogate. One follow-up probe per topic is usually enough.

### OPENING
Introduce yourself warmly. Explain that Tien-Ti asked you to have this conversation with the participant before the AI Activator program begins, and that he'll read everything personally. Make clear:
- There are no right or wrong answers
- They can skip any question at any time by saying "skip" or "pass" — no explanation needed
- The conversation takes about 15–20 minutes

Then ask for their name to get started — but explicitly note it's entirely optional if they'd prefer to stay anonymous.

### PHASE 1 — About you and your work
Ask one at a time:
1. When someone asks what they do at a backyard BBQ, what do they say?
2. What are the most repetitive or time-consuming parts of their job — the things they'd happily hand off if they could?
3. Who are their key stakeholders — internally and externally?
4. Do they lead or manage others, or are they primarily an individual contributor?

### PHASE 2 — Their AI starting point
1. How would they describe their current use of AI tools? Help them land on one of: (a) I've never tried it, (b) I've tried it once or twice out of curiosity, (c) I use it occasionally for simple tasks, (d) I use it regularly to structure my thinking and improve my work, (e) It's a core part of my daily workflow.
2. Which tools have they actually used? (ChatGPT, Gemini, Claude, Microsoft Copilot, other — or none)
3. Ask for a specific example where AI worked well for them — what exactly did they do and what happened? If they've never used AI, skip questions 4 and 5 entirely and go to Phase 3.
4. Ask for a specific example where AI let them down or frustrated them.
5. On a scale of 1–10, how confident do they feel right now in their ability to use AI effectively for their work?

### PHASE 3 — Blockers and concerns
1. What's the biggest blocker for them not using AI more? Weave these options naturally into the conversation — don't recite them as a list: data security / confidentiality; output quality and hallucinations; not knowing where to start; time and effort to learn; worried about what it means for my job; not seeing myself as a "tech person"; no real concerns.
2. Is there anything about AI that genuinely worries them — about their role, their team, or what it might mean for their industry? This is the open probe. Be comfortable with a thoughtful pause. If they mention job concerns, acknowledge directly and warmly before moving on: "That's a very understandable concern and you're not alone in feeling it — it's something the program addresses honestly, including where those concerns are well-founded and where they aren't."

### PHASE 4 — Hopes and expectations
1. If AI could meaningfully help with one specific task, what would it be?
2. Immediately follow up with: "If AI handled that for you, what would you choose to do with that time instead?" — this is an important question. If their answer is vague ("other work" / "I'm not sure"), probe gently once more: "Is there anything specific — a project you never get time for, or a part of your role you wish you could invest more in?"
3. What would success look like for them personally at the end of this program?

### PHASE 5 — Other
1. Anything else they'd like to share before they start?

### CLOSING
Thank them warmly and genuinely — not with hollow praise, but with a specific acknowledgement of something meaningful they shared. Tell them Tien-Ti will review the conversation before Day 1 and may follow up briefly if helpful. Let them know the program will be shaped in part by what they and their colleagues have shared. Wish them well.

Then immediately produce the structured summary — in the same response as the closing, after the separator line shown below.

## Handling skips and anonymity
If a participant says "skip", "pass", "rather not" or similar, respond simply with "No problem at all." and move to the next question. Note every skip in the summary. Never ask why they're skipping or push back.
If they prefer to remain anonymous, note this clearly in the summary.

## Branching logic

**"I've never used AI":** Skip Phase 2 questions 4 and 5. In Phase 3, open with "What's held you back from trying it so far?" rather than leading with blockers. In Phase 4, frame questions as "imagine if..." to make them concrete without assuming experience.

**"I use it extensively / it's core to my workflow":** Before moving to Phase 3, probe slightly deeper: "What's the most ambitious thing you've built or set up with AI so far?" and "Are you using anything beyond basic chat — Custom GPTs, agents, integrations?" These participants may be power users or potential informal champions.

**"I'm worried about my job":** Acknowledge directly and warmly. Don't dismiss, don't dwell. "That's a very understandable concern, and you're not alone. The program actually addresses this honestly — including where those concerns are well-founded and where they aren't." Then continue.

## Structured summary
When the conversation is complete, produce the summary in EXACTLY this format, preceded by the marker line shown. The summary is for Tien-Ti's eyes only.

---SUMMARY---
AI ACTIVATOR — PRE-PROGRAM PARTICIPANT BRIEF
Organisation: {ORG_NAME}
Generated: [date and time]

NAME: [name, or "Anonymous — participant preferred not to share"]
ROLE: [role]
SENIORITY: [Individual Contributor / Team Lead / Senior Leader / Unknown]
AI MATURITY: [1–5] — [1=Never used / 2=Tried once or twice / 3=Occasional / 4=Regular / 5=Core workflow]
CONFIDENCE SCORE: [x/10, or "Skipped"]

KEY STAKEHOLDERS:
[bullet list, or "Not discussed"]

TOP TIME-CONSUMING TASKS:
[bullet list]

AI USAGE:
  Tools used: [list, or "None"]
  Example — what worked: [specific example or "None shared"]
  Example — what didn't work: [specific example or "None shared"]

PRIMARY CONCERN: [one line]
DEEPER WORRIES: [summary of any job/industry anxieties, or "None raised"]

SPECIFIC TASK AI COULD HELP WITH: [their description of a task AI could help with]
IF AI FREED UP TIME, THEY WOULD: [preserve their exact words where possible — this is the most important field]
SUCCESS LOOKS LIKE: [their own definition]

OTHER NOTES: [anything else they wanted Tien-Ti to know, or "None"]

FLAGS FOR TIEN-TI:
[Notable signals: high anxiety, strong power user, sceptic, potential champion, interesting use case, anything requiring follow-up. If none: "None."]

QUESTIONS SKIPPED: [list, or "None"]
---END SUMMARY---
"""

# ── Helpers ────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_client():
    return Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])


def get_response(messages: list, org_name: str = "") -> str:
    client = get_client()
    # Inject org name into system prompt and use prompt caching
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
    """Pull the structured summary out of a response that contains it."""
    if "---SUMMARY---" in text and "---END SUMMARY---" in text:
        start = text.index("---SUMMARY---") + len("---SUMMARY---")
        end   = text.index("---END SUMMARY---")
        return text[start:end].strip()
    return None


def visible_text(text: str) -> str:
    """Strip the summary block from chat-visible text."""
    if "---SUMMARY---" in text:
        return text[:text.index("---SUMMARY---")].strip()
    return text


TRIGGER = "__BEGIN__"  # Hidden first turn used to prompt the opening greeting


# ── Email ──────────────────────────────────────────────────────────────────────
def send_summary_email(summary: str) -> bool:
    """
    Send the structured summary to Tien-Ti automatically.
    Returns True on success, False on failure.
    Participant does nothing — this fires server-side the moment
    the summary is generated.
    """
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
        return False  # Caller handles user-facing warning

# ── Session state init ─────────────────────────────────────────────────────────
if "messages"        not in st.session_state:
    st.session_state.messages        = []
if "summary"         not in st.session_state:
    st.session_state.summary         = None
if "complete"        not in st.session_state:
    st.session_state.complete        = False
if "pending_response" not in st.session_state:
    st.session_state.pending_response = False

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="diagnostic-header">
    <h2>AI Activator &mdash; Pre-Program Diagnostic</h2>
    <p>A private conversation to help Tien-Ti personalise your program &nbsp;·&nbsp; Approx. 15&ndash;20 minutes &nbsp;·&nbsp; You can skip any question</p>
    <div style="display:inline-block;background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.25);
                color:white;padding:0.25rem 0.9rem;border-radius:20px;font-size:0.85rem;margin-top:0.6rem;">
        📋 {ORG_NAME}
    </div>
</div>
""", unsafe_allow_html=True)

# ── Start button: only call API when user explicitly begins ───────────────────
# This prevents Streamlit warmup pings from triggering API calls.
if not st.session_state.messages:
    st.markdown(
        "<p style='text-align:center; color:#666; margin: 1rem 0 1.5rem;'>"
        "This private conversation takes about 15–20 minutes. "
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
        continue  # Never show the hidden trigger
    role    = msg["role"]
    display = visible_text(msg["content"])
    if not display:
        continue
    avatar = "💬" if role == "assistant" else "👤"
    with st.chat_message(role, avatar=avatar):
        st.write(display)

# ── Summary panel ──────────────────────────────────────────────────────────────
if st.session_state.summary:

    # Auto-send to Tien-Ti on first render of the summary (not on every rerun)
    if not st.session_state.get("email_sent"):
        st.session_state.email_sent = send_summary_email(st.session_state.summary)

    st.markdown("---")
    st.markdown("""
    <div class="complete-notice">
    ✅ &nbsp;<strong>You're all done — and your responses have been sent to Tien-Ti automatically.</strong>
    He'll review them before Day 1 and may drop you a quick note if he has any follow-up questions.
    Thanks for taking the time.
    </div>
    """, unsafe_allow_html=True)
    st.markdown("")

    # Offer a download so participants can keep their own copy if they want
    with st.expander("Want to keep a copy of your responses?"):
        filename = f"AI_Activator_PreProgram_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
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

    # Fallback notice if email failed
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
    # Process pending API response BEFORE rendering chat input.
    # This ensures the API call happens immediately after the user submits,
    # not on a subsequent passive rerun.
    if st.session_state.pending_response:
        st.session_state.pending_response = False
        with st.spinner(""):
            reply = get_response(st.session_state.messages, ORG_NAME)
        summary = extract_summary(reply)
        if summary:
            _ts = datetime.now().strftime("%d %b %Y  %H:%M")
            summary = re.sub(r"Generated:.*", f"Generated: {_ts}", summary)
            st.session_state.summary  = summary
            st.session_state.complete = True
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

    if user_input := st.chat_input("Type your response here…"):
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.pending_response = True  # Flag for next rerun
        st.rerun()
else:
    st.info("This conversation is complete. Thank you for your time!", icon="✅")

# ── Auto-scroll to bottom once conversation completes ─────────────────────────
# Guard with session flag so it only fires once, not on every rerun
if st.session_state.complete and not st.session_state.get("scrolled_to_bottom"):
    components.html("""
    <script>
        // Streamlit renders inside an iframe; window.parent is the real page.
        // section[data-testid="stMain"] is the scrollable container in Streamlit ≥1.30.
        var el = window.parent.document.querySelector('section[data-testid="stMain"]');
        if (!el) el = window.parent.document.querySelector('.main');
        if (el) el.scrollTop = el.scrollHeight;
    </script>
    """, height=0)
    st.session_state.scrolled_to_bottom = True
