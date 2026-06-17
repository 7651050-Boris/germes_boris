# Voice Message Handling in Telegram Bots

Pattern for receiving and transcribing voice messages in python-telegram-bot v22.x.

## Architecture

```
Voice message → download .ogg → ffmpeg convert to WAV → SpeechRecognition → text → process_query()
```

## Voice Handler Registration

```python
from telegram.ext import MessageHandler, filters

app.add_handler(MessageHandler(filters.VOICE, handle_voice))
```

## Handler Implementation

```python
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages — download, transcribe, query."""
    voice = update.message.voice
    if not voice:
        return

    await update.message.chat.send_action("typing")
    
    # Download voice file (.ogg format)
    file = await voice.get_file()
    ogg_path = f"/tmp/wagon_voice_{update.message.message_id}.ogg"
    await file.download_to_drive(ogg_path)
    
    # Transcribe
    text = await transcribe_voice(ogg_path)
    os.remove(ogg_path)
    
    if not text:
        await update.message.reply_text("🎤 Не удалось распознать речь. Попробуйте текстом.")
        return
    
    # Echo recognized text
    await update.message.reply_text(f"🎤 *{text}*", parse_mode="Markdown")
    
    # Feed into standard query pipeline
    await process_query(update, text)
```

## Transcription Function

`speech_recognition` is synchronous — must run in thread executor:

```python
import asyncio, subprocess
import speech_recognition as sr

FFMPEG_PATH = "/tmp/ffmpeg"  # Static ffmpeg binary

async def transcribe_voice(file_path: str) -> str:
    wav_path = file_path + ".wav"
    try:
        # Convert ogg → wav with ffmpeg
        subprocess.run(
            [FFMPEG_PATH, "-y", "-i", file_path, "-ac", "1", "-ar", "16000", wav_path],
            capture_output=True, timeout=15
        )
        
        # Blocking STT in thread
        loop = asyncio.get_event_loop()
        
        def _recognize():
            r = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio = r.record(source)
            return r.recognize_google(audio, language="ru-RU")
        
        return await loop.run_in_executor(None, _recognize)
    except Exception as e:
        print(f"Voice error: {e}")
        return ""
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)
```

## Requirements

```bash
pip3 install SpeechRecognition

# ffmpeg: download static binary from evermeet.cx (macOS)
curl -L "https://evermeet.cx/ffmpeg/getrelease/zip" -o /tmp/ffmpeg.zip
unzip -o /tmp/ffmpeg.zip -d /tmp
chmod +x /tmp/ffmpeg
```

## Key Points

- Telegram voice messages are `.ogg` (Opus codec) — need conversion to WAV
- Google Speech Recognition API used (free, no API key needed, `language="ru-RU"`)
- `speech_recognition` is BLOCKING — always use `asyncio.get_event_loop().run_in_executor(None, fn)`
- Transcribed text is echoed back to user (with 🎤 prefix) so they can verify recognition
- After transcription, feed into the same `process_query()` pipeline as text messages
