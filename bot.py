import os
import logging
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class AIChatBot:
    def __init__(self):
        # Get tokens from environment variables
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        
        # Initialize Gemini
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if gemini_api_key and gemini_api_key != 'your_gemini_api_key_here':
            genai.configure(api_key=gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-pro')
        else:
            self.gemini_model = None
            
        # Grok API key
        self.grok_api_key = os.getenv('GROK_API_KEY')
        if self.grok_api_key == 'your_grok_api_key_here':
            self.grok_api_key = None

    async def gemini_chat(self, message: str) -> str:
        """Gemini implementation"""
        if not self.gemini_model:
            return "❌ Gemini API key not configured. Please add GEMINI_API_KEY to environment variables."
            
        try:
            response = self.gemini_model.generate_content(message)
            return response.text
        except Exception as e:
            logger.error(f"Gemini Error: {e}")
            return f"❌ Gemini Error: {str(e)}"

    async def grok_chat(self, message: str) -> str:
        """Grok AI implementation"""
        if not self.grok_api_key:
            return "❌ Grok API key not configured. Please add GROK_API_KEY to environment variables."
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.grok_api_key}"
                    },
                    json={
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a helpful AI assistant."
                            },
                            {
                                "role": "user",
                                "content": message
                            }
                        ],
                        "model": "grok-beta",
                        "stream": False,
                        "temperature": 0.7
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data['choices'][0]['message']['content']
                else:
                    return f"❌ Grok API Error: {response.status_code} - {response.text}"
                    
        except Exception as e:
            logger.error(f"Grok Error: {e}")
            return f"❌ Grok Error: {str(e)}"

# Initialize the bot
ai_bot = AIChatBot()

async def start(update: Update, context: CallbackContext) -> None:
    """Send welcome message with beautiful AI selection buttons"""
    keyboard = [
        [
            InlineKeyboardButton("🔷 Gemini Pro", callback_data="gemini"),
            InlineKeyboardButton("🤖 Grok AI", callback_data="grok"),
        ],
        [
            InlineKeyboardButton("🔄 Both AIs", callback_data="both_ai"),
            InlineKeyboardButton("ℹ️ Help", callback_data="help"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = """
🌟 *Welcome to AI Assistant Bot!* 🌟

I'm your intelligent assistant powered by two amazing AI models:

🔷 *Gemini Pro* - Google's advanced AI
• Creative writing
• Code generation  
• Problem solving
• Research assistance

🤖 *Grok AI* - xAI's conversational expert
• Real-time conversations
• Technical discussions
• Creative brainstorming
• Knowledge sharing

✨ *Choose your AI companion below and let's create magic together!* ✨
    """
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def help_command(update: Update, context: CallbackContext) -> None:
    """Send help message"""
    help_text = """
🆘 *Help Guide* 🆘

*Available Commands:*
/start - Start the bot and choose AI
/help - Show this help message  
/switch - Switch between different AIs
/status - Check AI services status

*How to Use:*
1. 🎯 Use /start to choose your AI
2. 💬 Send any message to get AI responses
3. 🔄 Use /switch to change AI anytime
4. 📊 Use /status to check service health

*Supported AIs:*
• 🔷 Gemini Pro (Google)
• 🤖 Grok AI (xAI)
• 🔄 Both AIs (Compare responses)

*Tips:*
• Be specific in your questions
• Use clear language for better results
• You can ask follow-up questions
• Both AIs maintain conversation context

*Need Help?* Just type your question and I'll assist you! 🚀
    """
    
    keyboard = [
        [InlineKeyboardButton("🚀 Start Chatting", callback_data="start_chat")],
        [InlineKeyboardButton("🔷 Gemini", callback_data="gemini"), InlineKeyboardButton("🤖 Grok", callback_data="grok")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: CallbackContext) -> None:
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()
    
    choice = query.data
    
    if choice == "help":
        await help_command(update, context)
        return
    elif choice == "start_chat":
        await start(update, context)
        return
    
    # AI selection
    ai_choice = choice
    context.user_data['ai_choice'] = ai_choice
    
    ai_info = {
        'gemini': {
            'name': '🔷 Gemini Pro',
            'color': '#4285F4',
            'description': 'Google\'s most advanced AI model'
        },
        'grok': {
            'name': '🤖 Grok AI', 
            'color': '#FF6B35',
            'description': 'xAI\'s powerful conversational AI'
        },
        'both_ai': {
            'name': '🔄 Both AIs',
            'color': '#9C27B0',
            'description': 'Get responses from both Gemini and Grok'
        }
    }
    
    selected_ai = ai_info[ai_choice]
    
    confirmation_text = f"""
✅ *AI Selected: {selected_ai['name']}*

{selected_ai['description']}

💡 *Now you can start chatting!* Send me any message and I'll respond using {selected_ai['name']}.

🎯 *Examples you can try:*
• "Explain quantum computing"
• "Write a Python script for web scraping"  
• "Help me plan a trip to Japan"
• "What's the latest in AI research?"

✨ *Ready when you are!* ✨
    """
    
    keyboard = [
        [InlineKeyboardButton("📝 Start Chatting", callback_data="start_chat")],
        [InlineKeyboardButton("🔄 Switch AI", callback_data="switch_ai")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(confirmation_text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_message(update: Update, context: CallbackContext) -> None:
    """Handle user messages"""
    user_message = update.message.text
    user_id = update.message.from_user.id
    
    # Get AI choice from user data
    ai_choice = context.user_data.get('ai_choice', 'gemini')
    
    # Show typing action
    await update.message.chat.send_action(action="typing")
    
    try:
        if ai_choice == 'both_ai':
            # Get responses from both AIs
            responses = []
            
            # Gemini
            await update.message.chat.send_action(action="typing")
            gemini_response = await ai_bot.gemini_chat(user_message)
            responses.append(f"🔷 *Gemini Pro:*\n{gemini_response}")
            
            # Grok
            await update.message.chat.send_action(action="typing")
            grok_response = await ai_bot.grok_chat(user_message)
            responses.append(f"🤖 *Grok AI:*\n{grok_response}")
            
            final_response = "\n\n" + "═" * 30 + "\n\n".join(responses)
            
        elif ai_choice == 'gemini':
            gemini_response = await ai_bot.gemini_chat(user_message)
            final_response = f"🔷 *Gemini Pro:*\n{gemini_response}"
            
        elif ai_choice == 'grok':
            grok_response = await ai_bot.grok_chat(user_message)
            final_response = f"🤖 *Grok AI:*\n{grok_response}"
        
        # Split long messages (Telegram has 4096 character limit)
        if len(final_response) > 4000:
            for i in range(0, len(final_response), 4000):
                await update.message.reply_text(
                    final_response[i:i+4000], 
                    parse_mode='Markdown'
                )
        else:
            # Add quick action buttons
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Switch AI", callback_data="switch_ai"),
                    InlineKeyboardButton("❓ New Question", callback_data="new_question")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(final_response, parse_mode='Markdown', reply_markup=reply_markup)
            
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        error_text = """
❌ *Oops! Something went wrong.*

Please try one of these:
1. 🔄 Use /switch to change AI
2. 📝 Rephrase your question
3. ⏰ Try again in a moment

If the problem continues, use /help for assistance.
        """
        await update.message.reply_text(error_text, parse_mode='Markdown')

async def switch_ai(update: Update, context: CallbackContext) -> None:
    """Switch between AIs"""
    await start(update, context)

async def status_command(update: Update, context: CallbackContext) -> None:
    """Check AI services status"""
    status_text = """
📊 *AI Services Status*
"""
    
    # Check Gemini status
    if ai_bot.gemini_model:
        status_text += "🔷 *Gemini Pro:* ✅ Connected\n"
    else:
        status_text += "🔷 *Gemini Pro:* ❌ Not configured\n"
    
    # Check Grok status
    if ai_bot.grok_api_key:
        status_text += "🤖 *Grok AI:* ✅ Connected\n"
    else:
        status_text += "🤖 *Grok AI:* ❌ Not configured\n"
    
    ai_choice = context.user_data.get('ai_choice', 'gemini')
    ai_names = {'gemini': 'Gemini Pro', 'grok': 'Grok AI', 'both_ai': 'Both AIs'}
    
    status_text += f"\n💡 *Current Selection:* *{ai_names[ai_choice]}*\n\n"
    
    if ai_bot.gemini_model and ai_bot.grok_api_key:
        status_text += "🎯 All systems operational! Ready to assist you."
    else:
        status_text += "⚠️ Some services are not configured. Check environment variables."
    
    keyboard = [
        [InlineKeyboardButton("🔄 Switch AI", callback_data="switch_ai")],
        [InlineKeyboardButton("🚀 Start Chatting", callback_data="start_chat")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(status_text, parse_mode='Markdown', reply_markup=reply_markup)

def main() -> None:
    """Start the bot"""
    if not ai_bot.telegram_token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        return
    
    # Create Application
    application = Application.builder().token(ai_bot.telegram_token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("switch", switch_ai))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the Bot
    logger.info("🤖 Bot is starting...")
    logger.info("🔷 Gemini: " + ("✅ Configured" if ai_bot.gemini_model else "❌ Not configured"))
    logger.info("🤖 Grok: " + ("✅ Configured" if ai_bot.grok_api_key else "❌ Not configured"))
    logger.info("🚀 Bot is ready! Visit: t.me/btheai_abot")
    
    application.run_polling()

if __name__ == '__main__':
    main()
