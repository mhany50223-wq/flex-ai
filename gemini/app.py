import os
import time
try:
    from groq import Groq
except ImportError:
    Groq = None

from flask import Flask, jsonify, render_template, request

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

app = Flask(__name__)

SYSTEM_PROMPT = """You are FLEX, a professional and friendly AI assistant.
Reply in the same language as the user's latest message: Arabic for Arabic,
English for English, and use both naturally when the user mixes languages.
Help with general questions, learning, and programming. If you are unsure,
say so clearly. Do not claim to perform actions outside the conversation.
Use clean readable formatting. Do not wrap normal headings or sentences in
decorative asterisks. Use short headings, bullets, and code blocks only when
they genuinely improve readability."""


def get_groq_response(message, conversation):
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key or Groq is None:
        return None

    client = Groq(api_key=api_key)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for item in conversation[-8:]:
        role = item.get("role")
        content = item.get("content")

        if role in ("user", "assistant") and isinstance(content, str):
            messages.append({
                "role": role,
                "content": content[:2000],
            })

    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model=os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-20b"
        ),
        messages=messages,
        max_tokens=1000,
    )

    if response.choices:
        return response.choices[0].message.content

    return None


def get_ai_response(message, conversation):
    if genai is None:
        return "موقع FLEX يعمل بنجاح، لكن مكتبة Gemini غير مثبتة على الخادم."

    keys = [key.strip() for key in os.getenv("GEMINI_API_KEYS", "").split(",") if key.strip()]
    if not keys and os.getenv("GEMINI_API_KEY"):
        keys = [os.getenv("GEMINI_API_KEY")]
    if not keys:
        return "موقع FLEX يعمل بنجاح، لكن لم يتم إعداد GEMINI_API_KEY بعد. أضف مفتاح Gemini لتفعيل الردود الذكية."

    contents = []
    for item in conversation[-12:]:
        if item.get("role") in {"user", "assistant"} and isinstance(item.get("content"), str):
            contents.append({
                "role": "model" if item["role"] == "assistant" else "user",
                "parts": [{"text": item["content"][:4000]}],
            })
    contents.append({"role": "user", "parts": [{"text": message}]})

    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
    if not model:
        model = "gemini-3.8-flash"

    last_error = None

    for api_key in keys:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=120000),
        )

        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.7,
                    ),
                )

                if response and response.text:
                    return response.text

                break

            except Exception as error:
                last_error = error
                error_text = str(error).upper()

                retryable = any(code in error_text for code in (
                    "504",
                    "DEADLINE_EXCEEDED",
                    "503",
                    "UNAVAILABLE",
                    "502",
                    "BAD_GATEWAY",
                ))

                if retryable and attempt == 0:
                    time.sleep(2)
                    continue

                break

    # معالجة الخطأ والفولباك داخل الدالة بشكل صحيح
    if last_error:
        error_text = str(last_error).upper()

        fallback_errors = (
            "429",
            "RESOURCE_EXHAUSTED",
            "QUOTA",
            "503",
            "UNAVAILABLE",
            "504",
            "DEADLINE_EXCEEDED",
        )

        if any(code in error_text for code in fallback_errors):
            try:
                fallback_answer = get_groq_response(
                    message, conversation
                )

                if fallback_answer:
                    return fallback_answer

            except Exception:
                app.logger.exception("Groq fallback failed")

        raise last_error

    return "عذراً، لم نتمكن من الحصول على رد حالياً."


@app.get("/")
def home():
    return render_template("index.html")


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    conversation = data.get("conversation", [])

    if not message:
        return jsonify({"error": "اكتب رسالة أولًا."}), 400
    if len(message) > 4000:
        return jsonify({"error": "الرسالة طويلة جدًا. الحد الأقصى 4000 حرف."}), 400
    if not isinstance(conversation, list):
        conversation = []

    try:
        answer = get_ai_response(message, conversation)
        return jsonify({"answer": answer})
    except Exception as error:
        app.logger.exception("AI request failed: %s", error)
        error_msg = str(error)
        
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            user_error = "عذراً يا فلكس، مفتاح الـ API استنفذ الحد الأقصى اليومي (Quota). جرب مفتاح جديد أو انتظر قليلاً."
        elif "503" in error_msg or "UNAVAILABLE" in error_msg:
            user_error = "سيرفرات جوجل عليها ضغط حالياً (503)، جرب ابعت الرسالة تاني كمان ثانية."
        else:
            user_error = f"حدث خطأ مؤقت: {type(error).__name__}"

        return jsonify({"error": user_error}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
