import os
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from google import genai # या अपनी पसंद की AI लाइब्रेरी

# --- कॉन्फ़िगरेशन ---
# अपने टोकन को सुरक्षित रखें (आमतौर पर .env फ़ाइल से लोड किया जाता है)
BOT_TOKEN = "8846774051:AAFhJunFo1jd3azOs5jckXLRJvS-yKS30Hk" 
GEMINI_API_KEY = "AQ.Ab8RN6KfSREWDbY-4wEE_vRymAO6QYEwOuUYDc5pPHyCbWFoHg" # AI के लिए

# AI मॉडल को इनिशियलाइज़ करें
client = genai.Client(api_key=GEMINI_API_KEY)
model = client.models.get('gemini-2.5-flash') 

# --- कमांड हैंडलर फ़ंक्शंस ---

async def start(update, context):
    """/start कमांड को हैंडल करता है।"""
    await update.message.reply_text('नमस्ते! मैं आपका Study Helper Bot हूँ। मुझे नोट्स या ट्रिक्स के लिए कोई विषय बताएं, या "/quiz" टाइप करके क्विज़ शुरू करें।')

async def help_command(update, context):
    """/help कमांड को हैंडल करता है।"""
    help_text = (
        "📚 **Study Helper Bot कमांड्स:**\n"
        "/start - बातचीत शुरू करें\n"
        "/help - यह मदद मेनू देखें\n"
        "विषय टाइप करें - नोट्स या शॉर्ट ट्रिक्स प्राप्त करने के लिए (जैसे: 'History of India')\n"
        "/quiz - एक नया क्विज़ शुरू करें"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

# --- मुख्य फ़ंक्शन: नोट्स/ट्रिक्स और क्विज़ जेनरेट करना ---

async def handle_message(update, context):
    """उपयोगकर्ता के किसी भी टेक्स्ट मैसेज को हैंडल करता है।"""
    user_text = update.message.text.strip()
    
    # 1. नोट्स और शॉर्ट ट्रिक्स के लिए AI का उपयोग करना
    try:
        # यहाँ AI API कॉल का उदाहरण
        # prompt = f"मुझे '{user_text}' विषय पर संक्षिप्त नोट्स और एक शॉर्ट ट्रिक दें।"
        # response = model.generate_content(prompt)
        # bot_response = response.text
        
        # अभी के लिए एक साधारण प्रतिक्रिया:
        bot_response = f"⏳ मैं **{user_text}** पर नोट्स और ट्रिक्स जेनरेट कर रहा हूँ। AI का उपयोग करने के लिए आपको Gemini/OpenAI API को सेट अप करना होगा।"
        
    except Exception as e:
        # AI API में त्रुटि होने पर
        bot_response = f"क्षमा करें, नोट्स जेनरेट करते समय एक त्रुटि हुई: {e}"

    await update.message.reply_text(bot_response)

async def start_quiz(update, context):
    """/quiz कमांड को हैंडल करता है और क्विज़ शुरू करता है।"""
    # 2. क्विज़ जेनरेट करने के लिए AI का उपयोग करना
    
    # यहाँ AI API कॉल का उदाहरण
    # prompt = "मुझे 3 बहुविकल्पीय प्रश्न (MCQs) 'Science' विषय पर जेनरेट करके दें, साथ में सही उत्तर भी दें।"
    # response = model.generate_content(prompt)
    # quiz_data = response.text # AI से प्राप्त प्रश्न और उत्तर
    
    # Telegram की 'send_poll' सुविधा का उपयोग करके क्विज़ प्रश्न भेजें
    question = "भारत की राजधानी क्या है?"
    options = ["मुंबई", "कोलकाता", "नई दिल्ली", "चेन्नई"]
    correct_option_id = 2  # 'नई दिल्ली' का इंडेक्स (0 से शुरू)
    
    await context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question=question,
        options=options,
        is_anonymous=False, # क्विज़ के लिए इसे False रखें
        type='quiz',
        correct_option_id=correct_option_id,
        explanation="नई दिल्ली भारत की राजधानी है।"
    )

# --- मुख्य फ़ंक्शन: बॉट शुरू करना ---

def main():
    """बॉट को शुरू करता है।"""
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # कमांड हैंडलर जोड़ें
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("quiz", start_quiz))

    # टेक्स्ट मैसेज हैंडलर जोड़ें (यह नोट्स/ट्रिक्स के लिए है)
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("बॉट शुरू हो रहा है...")
    # बॉट को निरंतर सुनना शुरू करें
    application.run_polling()

if __name__ == '__main__':
    # सुनिश्चित करें कि आपने BOT_TOKEN और AI API Key को सही ढंग से सेट किया है।
    main()