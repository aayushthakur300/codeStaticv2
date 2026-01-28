import asyncio
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr, BaseModel

# ⚠️ REPLACE THESE WITH YOUR EXACT RENDER CREDENTIALS
conf = ConnectionConfig(
    MAIL_USERNAME = "codestatic.ai@gmail.com", # YOUR REAL GMAIL
    MAIL_PASSWORD = "ungygdxzpjztqavc",       # YOUR 16-DIGIT APP PASSWORD
    MAIL_FROM = "codestatic.ai@gmail.com",     # MUST MATCH USERNAME
    MAIL_PORT = 465,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_STARTTLS = False,
    MAIL_SSL_TLS = True,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

async def simple_send():
    print("⏳ Attempting to send email...")
    
    message = MessageSchema(
        subject="Test Email from Render Debug",
        recipients=["aayushthakur300@gmail.com"], # Send to yourself
        body="If you can read this, the email logic is working!",
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    
    try:
        await fm.send_message(message)
        print("✅ SUCCESS: Email sent successfully!")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(simple_send())