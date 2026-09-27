import json
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from google import genai
from google.genai import types

# ----------------- अपनी Keys यहाँ डालें -----------------
BOT_TOKEN = "8846774051:AAFhJunFo1jd3azOs5jckXLRJvS-yKS30Hk"
GEMINI_API_KEY = "AQ.Ab8RN6KfSREWDbY-4wEE_vRymAO6QYEwOuUYDc5pPHyCbWFoHg"
# --------------------------------------------------------

# Gemini क्लाइंट
ai_client = genai.Client(api_key=GEMINI_API_KEY)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update, context):
    welcome_text = (
        "👋 **नमस्ते! मैं आपका AI Study Helper Bot हूँ।**\n\n"
        "📖 **नोट्स और ट्रिक्स के लिए:** बस कोई भी टॉपिक लिखकर भेजें (उदा: *Photosynthesis*, *Mughal Empire*)\n\n"
        "🎯 **क्विज़ के लिए:** `/quiz` या `/quiz Biology` लिखें।"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def handle_notes(update, context):
    user_topic = update.message.text.strip()
    status_msg = await update.message.reply_text(f"⏳ **{user_topic}** पर नोट्स और ट्रिक्स तैयार कर रहा हूँ...")

    prompt = f"""
    आप एक बेहतरीन शिक्षक हैं। विद्यार्थी ने टॉपिक दिया है: "{user_topic}".
    कृपया निम्नलिखित फॉर्मेट में हिंदी और हिंग्लिश में जवाब दें:
    
    📌 **मुख्य बिंदु (Key Notes):** (3-4 सबसे ज़रूरी बातें)
    💡 **याद रखने की शॉर्ट ट्रिक (Memory Trick):** (आसान और मजेदार ट्रिक)
    ⚠️ **महत्वपूर्ण तथ्य (Exam Tip):** (एक ज़रूरी परीक्षा बिंदु)
    """

    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        await status_msg.edit_text(response.text, parse_mode='Markdown')
    except Exception as e:
        await status_msg.edit_text(f"❌ त्रुटि: {e}")

async def generate_quiz(update, context):
    topic = "General Knowledge / Science / Math"
    if context.args:
        topic = " ".join(context.args)

    status_msg = await update.message.reply_text(f"🎲 **{topic}** पर सवाल तैयार हो रहा है...")

    prompt = f"""
    Generate one multiple-choice quiz question on: "{topic}".
    Provide strictly JSON without markdown:
    {{
      "question": "Question text?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_index": 0,
      "explanation": "Short reason"
    }}
    Note: correct_index must be 0, 1, 2, or 3.
    """

    try:
        response = ai_client.models.generate_content(
            model='gemini-3.8-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        quiz_data = json.loads(response.text)
        await status_msg.delete()

        await context.bot.send_poll(
            chat_id=update.effective_chat.id,
            question=quiz_data["question"],
            options=quiz_data["options"],
            is_anonymous=False,
            type='quiz',
            correct_option_id=int(quiz_data["correct_index"]),
            explanation=quiz_data.get("explanation", "सही उत्तर!"),
        )
    except Exception as e:
        await status_msg.edit_text(f"❌ क्विज़ जनरेट करने में त्रुटि: {e}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quiz", generate_quiz))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_notes))

    print("✅ बॉट सफलतापूर्वक चालू हो गया है! Telegram पर टेस्ट करें...")
    app.run_polling()

if __name__ == '__main__':
    main()
