"""
ai.py — Google Gemini AI integration for Spark Assistant
"""
import google.generativeai as genai
import config

genai.configure(api_key=config.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


def ask(question: str, context: str = "") -> str:
    """Answer a general question, with optional context."""
    prompt = f"{context}\n\nQuestion: {question}" if context else question
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ AI error: {e}"


def reflect_on_journal(entries_text: str) -> str:
    """Give a warm, personal reflection on recent journal entries."""
    prompt = f"""You are a caring personal coach. Read these journal entries and give a warm, insightful reflection in 150-200 words. Note emotional patterns, highlight strengths, and gently suggest 1-2 actionable ideas. Be encouraging and personal.

Journal entries:
{entries_text}

Your reflection:"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ AI error: {e}"


def weekly_review(goals_text: str, journal_text: str) -> str:
    """Generate a full weekly review combining goals + journal."""
    prompt = f"""You are a personal coach doing a weekly review. Write:
1. A brief summary of what the week looked like
2. Progress on goals — celebrate wins, encourage ongoing ones
3. Key emotional themes from the journal
4. 2-3 specific, actionable suggestions for the coming week

Keep it warm, personal, and under 300 words.

GOALS:
{goals_text}

JOURNAL (recent entries):
{journal_text}

Weekly Review:"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ AI error: {e}"
