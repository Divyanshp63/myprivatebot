import os
import json
import random
import logging
import asyncio
import threading
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from google import genai
from google.genai import types

# ----------------- 1. Dummy Web Server (Render 24/7) -----------------
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "RRB NTPC Study Bot is 100% Active!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web, daemon=True).start()

# ----------------- 2. API Keys & Setup -----------------
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8846774051:AAFhJunFo1jd3azOs5jckXLRJvS-yKS30Hk")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6KfSREWDbY-4wEE_vRymAO6QYEwOuUYDc5pPHyCbWFoHg")

ai_client = genai.Client(api_key=GEMINI_API_KEY)
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# Primary aur Fallback models list
MODELS_TO_TRY = ['gemini-3.8-flash', 'gemini-3-flash', 'gemini-1.5-flash-8b']

# ----------------- 3. Offline Backup PYQ Bank -----------------
# Agar Google API temporary 100% fail ho jaye, toh user ko inme se authentic Railway PYQ turant mil jayega
OFFLINE_PYQ_BANK = [
    {
        "question": "RRB NTPC: 1857 ke vidroh ke samay Bharat ka Governor-General kaun tha?",
        "options": ["Lord Canning", "Lord Dalhousie", "Lord Curzon", "Lord William Bentinck"],
        "correct_index": 0,
        "explanation": "Lord Canning 1857 ke vidroh ke samay Governor-General tha, aur baad mein Bharat ka pehla Viceroy bana."
    },
    {
        "question": "RRB NTPC: Ek train 72 km/h ki raftaar se 200m lambe bridge ko 20 second mein paar karti hai. Train ki lambai kya hai?",
        "options": ["200 m", "250 m", "150 m", "300 m"],
        "correct_index": 0,
        "explanation": "Speed = 72 * (5/18) = 20 m/s. Kul doori = 20 * 20 = 400m. Train ki lambai = 400 - 200 = 200m."
    },
    {
        "question": "RRB NTPC: Paani ka maximum density (adhiktam ghantva) kis tapmaan par hota hai?",
        "options": ["0°C", "4°C", "100°C", "-4°C"],
        "correct_index": 1,
        "explanation": "Paani ka adhiktam ghantva 4°C (ya 277 Kelvin) par hota hai."
    },
    {
        "question": "RRB NTPC: Bharatiya Samvidhan mein 'Maulik Adhikar' (Fundamental Rights) kis desh se liye gaye hain?",
        "options": ["USA", "Russia", "UK", "Canada"],
        "correct_index": 0,
        "explanation": "Fundamental Rights United States (USA) ke Samvidhan se liye gaye hain (Bhag 3, Article 12-35)."
    }
]

# ----------------- 4. Bulletproof AI Engine -----------------
async def call_gemini_safe(prompt, as_json=False):
    """Multiple models try karega aur backoff retry ke saath run karega."""
    config = types.GenerateContentConfig(response_mime_type="application/json") if as_json else None
    
    for model_name in MODELS_TO_TRY:
        for attempt in range(2):  # Har model ko 2 chances
            try:
                response = ai_client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                logging.warning(f"Model {model_name} attempt {attempt+1} failed: {e}")
                await asyncio.sleep(1.5)  # Thoda wait karke retry
                continue
                
    return None  # Saare models fail ho gaye

# ----------------- 5. Handlers -----------------
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

    res_text = await call_gemini_safe(prompt=prompt, as_json=False)
    
    if res_text:
        try:
            await status_msg.edit_text(res_text, parse_mode='Markdown')
        except Exception:
            # Markdown parsing issue se bachne ke liye plain text fallback
            await status_msg.edit_text(res_text)
    else:
        # User ko error code dikhane ke bajay friendly study tip
        fallback_msg = (
            f"📘 **RRB NTPC Rapid Revision: {topic}**\n\n"
            "⚠️ AI servers par temporary load spike hai, par aapki padhai rukni nahi chahiye:\n"
            "• Is topic ke previous year railway questions ko speed tests ke saath practice karein.\n"
            "• Formulas aur shortcut tricks revise karein.\n\n"
            "💡 Dobara command bhejein ya `/pyq` attempt karein!"
        )
        await status_msg.edit_text(fallback_msg)

async def handle_pyq_quiz(update, context):
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

    quiz_data = None
    res_text = await call_gemini_safe(prompt=prompt, as_json=True)

    if res_text:
        try:
            # Agar codeblocks aa jayein toh clean karna
            clean_json = res_text.replace("```json", "").replace("```", "").strip()
            quiz_data = json.loads(clean_json)
        except Exception as parse_err:
            logging.error(f"JSON Parse error: {parse_err}")
            quiz_data = None

    # Agar AI down ho ya JSON galat ho, Offline PYQ Bank se direct pick karega
    if not quiz_data:
        logging.info("Serving from offline backup bank...")
        quiz_data = random.choice(OFFLINE_PYQ_BANK)

    try:
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
        logging.error(f"Failed to send poll: {e}")
        await update.message.reply_text("Quiz load hone mein dikkat aayi. Kripya ek baar fir `/quiz` type karein.")

# ----------------- 6. Main App -----------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pyq", handle_pyq_quiz))
    app.add_handler(CommandHandler("quiz", handle_pyq_quiz))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_ntpc_notes))

    print("✅ RRB NTPC AI Bot chalu ho chuka hai (Zero-Error Mode Active)!")
    app.run_polling()

if __name__ == '__main__':
    main()
