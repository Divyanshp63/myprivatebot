import os
import json
import logging
import asyncio
import threading
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from google import genai
from google.genai import types
from google.genai.errors import APIError

# ----------------- 1. Dummy Web Server (Render 24/7 ke liye) -----------------
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "RRB NTPC Study Bot is Alive!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web, daemon=True).start()

# ----------------- 2. API Keys & Client -----------------
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8846774051:AAFhJunFo1jd3azOs5jckXLRJvS-yKS30Hk")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6KfSREWDbY-4wEE_vRymAO6QYEwOuUYDc5pPHyCbWFoHg")

ai_client = genai.Client(api_key=GEMINI_API_KEY)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Stable fast model name
MODEL_NAME = 'gemini-2.5-flash'

async def generate_with_retry(prompt, config=None, retries=3, delay=2):
    """503 Server Busy ke liye automatic backoff retry function"""
    for attempt in range(retries):
        try:
            kwargs = {"model": MODEL_NAME, "contents": prompt}
            if config:
                kwargs["config"] = config
            response = ai_client.models.generate_content(**kwargs)
            return response
        except APIError as e:
            if getattr(e, 'code', None) == 503 or "503" in str(e) or "UNAVAILABLE" in str(e):
                logging.warning(f"503 Server Busy. Retrying in {delay}s... (Attempt {attempt+1}/{retries})")
                await asyncio.sleep(delay)
                delay *= 2
            else:
                raise e
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                await asyncio.sleep(delay)
                delay *= 2
            else:
                raise e
    raise Exception("Model par load zyada hai. Kripya 1 minute baad try karein.")

# ----------------- 3. Handlers -----------------
async def start(update, context):
    welcome_text = (
        "🚂 **RRB NTPC AI Study Partner mein aapka swagat hai!**\n\n"
        "🎯 **Railway PYQ Quizzes ke liye:**\n"
        "• `/pyq math` - Maths ke previous year questions\n"
        "• `/pyq gk` - Static GK, Polity, History, Current\n"
        "• `/pyq gs` - General Science (Physics, Chem, Bio)\n"
        "• `/quiz` - Random NTPC CBT Level Quiz\n\n"
        "📖 **Concept + Short Tricks ke liye:**\n"
        "Bas koi bhi topic ka naam likhkar bhejein (jaise: *Time and Work*, *Blood Relation*, *Buddhism*, *Periodic Table*)."
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def handle_ntpc_notes(update, context):
    """RRB NTPC specific notes, formulas and shortcut tricks"""
    topic = update.message.text.strip()
    status_msg = await update.message.reply_text(f"⏳ **{topic}** (RRB NTPC Special) taiyar ho raha hai...")

    prompt = f"""
    Aap Railway Recruitment Board (RRB NTPC CBT-1 & CBT-2) ke top-rank teacher hain.
    Topic: "{topic}".
    
    Kripya Hindi aur Hinglish mein strictly is structure mein clear format provide karein:
    
    📘 **RRB NTPC Core Concept (Mukhya Bindu):**
    (2-3 exam-relevant points jo directly exam mein puche jaate hain)
    
    ⚡ **Exam Shortcut Trick / Formula (Fast Method):**
    (Agar Math/Reasoning hai toh 10-15 seconds solve karne ka direct shortcut; agar GK/GS hai toh yaad rakhne ki trick/mnemonic)
    
    📝 **NTPC Pattern Model Question:**
    (Ek railway level question aur uska quick solution)
    """

    try:
        response = await generate_with_retry(prompt=prompt)
        await status_msg.edit_text(response.text, parse_mode='Markdown')
    except Exception as e:
        await status_msg.edit_text(f"⚠️ Server busy hai: {e}")

async def handle_pyq_quiz(update, context):
    """RRB NTPC Previous Year Questions as native Telegram Quiz Poll"""
    subject = "General Awareness & Science & Maths"
    if context.args:
        arg = context.args[0].lower()
        if arg in ["math", "maths"]:
            subject = "Mathematics (Arithmetic, Advance Maths)"
        elif arg == "gk":
            subject = "General Awareness (History, Polity, Geography, Static GK)"
        elif arg == "gs":
            subject = "General Science (Class 9th-10th Level Physics, Chemistry, Biology)"

    status_msg = await update.message.reply_text(f"🎯 **RRB NTPC ({subject})** ka PYQ la raha hoon...")

    prompt = f"""
    Generate exactly ONE authentic Multiple Choice Question strictly matching RRB NTPC CBT-1 / CBT-2 previous year papers for subject: "{subject}".
    
    Provide output ONLY as valid JSON (no markdown formatting, no codeblocks):
    {{
      "question": "Question text in Hindi / English with exam-level accuracy?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_index": 0,
      "explanation": "Short 1-2 line explanation or calculation trick."
    }}
    Rules:
    - correct_index must be an integer between 0 and 3.
    - Each option must be under 95 characters.
    - The question should feel like an actual railway exam paper question.
    """

    try:
        config = types.GenerateContentConfig(response_mime_type="application/json")
        response = await generate_with_retry(prompt=prompt, config=config)
        quiz_data = json.loads(response.text)
        await status_msg.delete()

        await context.bot.send_poll(
            chat_id=update.effective_chat.id,
            question=quiz_data["question"][:295],
            options=quiz_data["options"][:4],
            is_anonymous=False,
            type='quiz',
            correct_option_id=int(quiz_data["correct_index"]),
            explanation=quiz_data.get("explanation", "Right Answer!")[:195],
        )
    except Exception as e:
        await status_msg.edit_text(f"❌ PYQ lane mein error: {e}")

# ----------------- 4. Main App -----------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pyq", handle_pyq_quiz))
    app.add_handler(CommandHandler("quiz", handle_pyq_quiz))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_ntpc_notes))

    print("✅ RRB NTPC AI Bot chalu ho chuka hai!")
    app.run_polling()

if __name__ == '__main__':
    main()
