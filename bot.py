"""
bot.py — Spark Assistant: Your Personal AI Telegram Bot

Commands:
  /start              — Welcome & help menu
  /help               — Show all commands

  Goals:
  /goal add <text>    — Add a new goal
  /goal list          — List active goals
  /goal done <id>     — Mark goal as completed
  /goal note <id> <n> — Log progress on a goal
  /goal all           — All goals (incl. completed)
  /goal delete <id>   — Delete a goal
  /goal report        — AI-generated goals summary

  Journal:
  /journal <text>     — Save a journal entry
  /journal show       — Show recent 5 entries
  /journal search <w> — Search entries by keyword
  /reflect            — AI reflects on your journal

  AI:
  /ask <question>     — Ask Gemini anything
  /week               — Full weekly review
"""

import logging
import os

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode

import config
import database as db
import ai

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("assistant.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def uid(update: Update) -> int:
    return update.effective_user.id


# ── /start & /help ────────────────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    db.init_db()
    welcome = (
        "✨ *Spark Assistant — Your Personal AI Coach*\n\n"
        "I help you track goals, journal your thoughts, and answer anything.\n\n"
        "🎯 *Goals*\n"
        "`/goal add <your goal>` — Add a goal\n"
        "`/goal list` — See active goals\n"
        "`/goal done <id>` — Mark as completed ✅\n"
        "`/goal note <id> <note>` — Log progress\n"
        "`/goal all` — All goals incl. completed\n"
        "`/goal report` — AI goal summary\n\n"
        "📔 *Journal*\n"
        "`/journal <your thoughts>` — Save an entry\n"
        "`/journal show` — See recent entries\n"
        "`/journal search <word>` — Search past entries\n"
        "`/reflect` — AI reflects on your journal\n\n"
        "💬 *Ask AI*\n"
        "`/ask <question>` — Ask Gemini anything\n"
        "`/week` — Full weekly review\n\n"
        "_Let's grow together, one day at a time._ 🌱"
    )
    await update.message.reply_text(welcome, parse_mode=ParseMode.MARKDOWN)


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await cmd_start(update, ctx)


# ── /goal ─────────────────────────────────────────────────────────────────────
async def cmd_goal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args    = ctx.args
    user_id = uid(update)

    if not args:
        await update.message.reply_text(
            "🎯 *Goal Commands:*\n"
            "`/goal add <text>` — Add a goal\n"
            "`/goal list` — Active goals\n"
            "`/goal done <id>` — Mark complete\n"
            "`/goal note <id> <note>` — Log progress\n"
            "`/goal all` — All goals\n"
            "`/goal delete <id>` — Delete\n"
            "`/goal report` — AI summary",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    sub = args[0].lower()

    # /goal add <text>
    if sub == "add":
        if len(args) < 2:
            await update.message.reply_text(
                "Usage: `/goal add <your goal>`", parse_mode=ParseMode.MARKDOWN
            )
            return
        title   = " ".join(args[1:])
        goal_id = db.add_goal(user_id, title)
        await update.message.reply_text(
            f"🎯 *Goal #{goal_id} added!*\n`{title}`\n\n"
            f"_Track progress: `/goal note {goal_id} <what you did>`_",
            parse_mode=ParseMode.MARKDOWN,
        )

    # /goal list
    elif sub == "list":
        goals = db.list_goals(user_id)
        if not goals:
            await update.message.reply_text(
                "No active goals yet.\nAdd one: `/goal add <your goal>`",
                parse_mode=ParseMode.MARKDOWN,
            )
            return
        lines = ["🎯 *Your Active Goals:*\n"]
        for g in goals:
            lines.append(f"*#{g['id']}* {g['title']}")
            if g["progress_notes"]:
                last = g["progress_notes"].strip().split("\n")[-1]
                lines.append(f"   ↳ _{last}_")
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

    # /goal all
    elif sub == "all":
        goals = db.all_goals(user_id)
        if not goals:
            await update.message.reply_text(
                "No goals yet! `/goal add <text>`", parse_mode=ParseMode.MARKDOWN
            )
            return
        active = [g for g in goals if not g["completed"]]
        done   = [g for g in goals if g["completed"]]
        lines  = []
        if active:
            lines.append("🎯 *Active Goals:*")
            for g in active:
                lines.append(f"*#{g['id']}* {g['title']}")
        if done:
            lines.append("\n✅ *Completed Goals:*")
            for g in done:
                lines.append(f"#{g['id']} ~~{g['title']}~~")
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

    # /goal done <id>
    elif sub == "done":
        if len(args) < 2 or not args[1].isdigit():
            await update.message.reply_text(
                "Usage: `/goal done <id>`", parse_mode=ParseMode.MARKDOWN
            )
            return
        goal_id = int(args[1])
        if db.complete_goal(user_id, goal_id):
            await update.message.reply_text(
                f"🎉 *Goal #{goal_id} completed!*\n\nYou did it! Keep that momentum going. 🚀",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            await update.message.reply_text(f"Goal #{goal_id} not found.")

    # /goal note <id> <note>
    elif sub == "note":
        if len(args) < 3 or not args[1].isdigit():
            await update.message.reply_text(
                "Usage: `/goal note <id> <your progress note>`",
                parse_mode=ParseMode.MARKDOWN,
            )
            return
        goal_id = int(args[1])
        note    = " ".join(args[2:])
        if db.add_goal_note(user_id, goal_id, note):
            await update.message.reply_text(
                f"📝 Progress noted on Goal #{goal_id}!\n_{note}_",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            await update.message.reply_text(f"Goal #{goal_id} not found.")

    # /goal delete <id>
    elif sub == "delete":
        if len(args) < 2 or not args[1].isdigit():
            await update.message.reply_text(
                "Usage: `/goal delete <id>`", parse_mode=ParseMode.MARKDOWN
            )
            return
        goal_id = int(args[1])
        if db.delete_goal(user_id, goal_id):
            await update.message.reply_text(f"🗑 Goal #{goal_id} deleted.")
        else:
            await update.message.reply_text(f"Goal #{goal_id} not found.")

    # /goal report
    elif sub == "report":
        goals = db.all_goals(user_id)
        if not goals:
            await update.message.reply_text(
                "No goals yet! `/goal add <text>`", parse_mode=ParseMode.MARKDOWN
            )
            return
        await update.message.reply_text(
            "🤖 _Generating your goals report..._", parse_mode=ParseMode.MARKDOWN
        )
        goals_text = "\n".join(
            [
                f"{'✅' if g['completed'] else '🎯'} #{g['id']}: {g['title']}"
                + (f"\n   Progress notes: {g['progress_notes']}" if g["progress_notes"] else "")
                for g in goals
            ]
        )
        result = ai.ask(
            "Give me a warm, encouraging analysis of my goals. Celebrate wins, highlight what's in progress, and suggest clear next steps for each active goal. Under 250 words.",
            context=f"My goals:\n{goals_text}",
        )
        await update.message.reply_text(
            f"📊 *Goals Report*\n\n{result}", parse_mode=ParseMode.MARKDOWN
        )

    else:
        await update.message.reply_text(
            "Unknown sub-command. Type `/goal` to see options.", parse_mode=ParseMode.MARKDOWN
        )


# ── /journal ──────────────────────────────────────────────────────────────────
async def cmd_journal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args    = ctx.args
    user_id = uid(update)

    if not args:
        await update.message.reply_text(
            "📔 *Journal Commands:*\n"
            "`/journal <your thoughts>` — Save entry\n"
            "`/journal show` — Recent 5 entries\n"
            "`/journal search <keyword>` — Search\n"
            "`/reflect` — AI reflection on your journal",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    sub = args[0].lower()

    # /journal show
    if sub == "show":
        entries = db.list_journal(user_id, 5)
        if not entries:
            await update.message.reply_text(
                "No entries yet!\nWrite one: `/journal <your thoughts>`",
                parse_mode=ParseMode.MARKDOWN,
            )
            return
        lines = ["📔 *Recent Journal Entries:*\n"]
        for e in reversed(entries):
            lines.append(f"🗓 _{e['created_at']}_\n{e['entry']}\n{'─' * 20}")
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

    # /journal search <keyword>
    elif sub == "search":
        if len(args) < 2:
            await update.message.reply_text(
                "Usage: `/journal search <keyword>`", parse_mode=ParseMode.MARKDOWN
            )
            return
        keyword = " ".join(args[1:])
        entries = db.search_journal(user_id, keyword)
        if not entries:
            await update.message.reply_text(
                f'No entries found matching *"{keyword}"*.',
                parse_mode=ParseMode.MARKDOWN,
            )
            return
        lines = [f'🔍 *Results for "{keyword}":*\n']
        for e in entries:
            lines.append(f"🗓 _{e['created_at']}_\n{e['entry']}\n{'─' * 20}")
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

    # /journal <any text> — save entry
    else:
        entry    = " ".join(args)
        entry_id = db.add_journal(user_id, entry)
        await update.message.reply_text(
            f"📔 *Journal saved!* _(Entry #{entry_id})_\n\n_{entry}_\n\n"
            "_Type `/reflect` for AI insights on your recent entries._",
            parse_mode=ParseMode.MARKDOWN,
        )


# ── /reflect ──────────────────────────────────────────────────────────────────
async def cmd_reflect(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id     = uid(update)
    entries_txt = db.recent_journal_text(user_id, 10)
    if entries_txt == "No journal entries yet.":
        await update.message.reply_text(
            "No journal entries yet!\nWrite some first: `/journal <your thoughts>`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    await update.message.reply_text(
        "🤖 _Reading your journal and reflecting..._", parse_mode=ParseMode.MARKDOWN
    )
    reflection = ai.reflect_on_journal(entries_txt)
    await update.message.reply_text(
        f"🪞 *Reflection*\n\n{reflection}", parse_mode=ParseMode.MARKDOWN
    )


# ── /ask ──────────────────────────────────────────────────────────────────────
async def cmd_ask(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text(
            "Usage: `/ask <your question>`\n\nExample: `/ask What's the best way to build discipline?`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    question = " ".join(ctx.args)
    await update.message.reply_text("🤖 _Thinking..._", parse_mode=ParseMode.MARKDOWN)
    answer = ai.ask(question)
    if len(answer) > 4000:
        answer = answer[:4000] + "..."
    await update.message.reply_text(f"💬 {answer}")


# ── /week ─────────────────────────────────────────────────────────────────────
async def cmd_week(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id      = uid(update)
    goals        = db.all_goals(user_id)
    journal_text = db.recent_journal_text(user_id, 14)

    if not goals and journal_text == "No journal entries yet.":
        await update.message.reply_text(
            "Nothing to review yet! Start by:\n"
            "• Adding goals: `/goal add <goal>`\n"
            "• Writing journal: `/journal <thoughts>`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    await update.message.reply_text(
        "🤖 _Preparing your weekly review..._", parse_mode=ParseMode.MARKDOWN
    )
    goals_text = (
        "\n".join(
            [
                f"{'✅' if g['completed'] else '🎯'} #{g['id']}: {g['title']}"
                + (f"\n   Progress: {g['progress_notes']}" if g["progress_notes"] else "")
                for g in goals
            ]
        )
        if goals
        else "No goals set yet."
    )
    review = ai.weekly_review(goals_text, journal_text)
    await update.message.reply_text(
        f"📋 *Your Weekly Review*\n\n{review}", parse_mode=ParseMode.MARKDOWN
    )


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if config.TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("\n❌ Please set your TELEGRAM_BOT_TOKEN in config.py or as an env variable on Railway!")
        return

    db.init_db()
    logger.info("Starting Spark Assistant...")

    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("help",    cmd_help))
    app.add_handler(CommandHandler("goal",    cmd_goal))
    app.add_handler(CommandHandler("journal", cmd_journal))
    app.add_handler(CommandHandler("reflect", cmd_reflect))
    app.add_handler(CommandHandler("ask",     cmd_ask))
    app.add_handler(CommandHandler("week",    cmd_week))

    logger.info("✅ All command handlers registered.")
    logger.info("Spark Assistant is running. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
