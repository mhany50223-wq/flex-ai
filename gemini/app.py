import os

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


import time

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

    # الالتزام التام بموديل 3.8-flash حصراً زي ما جوجل طالبة
    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
    if not model:
        model = "gemini-3.8-flash"

    last_error = None

    # الدوران على مفاتيح الـ API الأربعة لتجاوز أي ضغط مؤقت (503)
    for api_key in keys:
        try:
            client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(timeout=10000),
            )
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
        except Exception as error:
            last_error = error
            # لو المفتاح ده جاب ضغط 503، بينقل للمفتاح اللي بعده فوراً
            continue

    if last_error:
        raise last_error
    return "عذراً، لم نتمكن من الحصول على رد حالياً. يرجى المحاولة لاحقاً."


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
        details = str(error)
        for api_key in os.getenv("GEMINI_API_KEYS", "").split(",") + [os.getenv("GEMINI_API_KEY", "")]:
            if api_key:
                details = details.replace(api_key, "[hidden]")
        return jsonify({
            "error": f"حدث خطأ من Gemini: {type(error).__name__}: {details[:500]}"
        }), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
