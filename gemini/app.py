import os

from flask import Flask, jsonify, render_template, request

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

app = Flask(__name__)

SYSTEM_PROMPT = """أنت مساعد ذكي داخل موقع خاص. أجب بالعربية بشكل واضح وودود،
وساعد المستخدم في الأسئلة العامة والبرمجة. إذا لم تعرف الإجابة فقل ذلك بوضوح.
لا تدّعِ أنك تنفذ أفعالًا خارج المحادثة."""


def get_ai_response(message, conversation):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or genai is None:
        return "موقع FLEX يعمل بنجاح، لكن لم يتم إعداد GEMINI_API_KEY بعد. أضف مفتاح Gemini لتفعيل الردود الذكية."

    client = genai.Client(api_key=api_key)
    contents = []
    for item in conversation[-12:]:
        if item.get("role") in {"user", "assistant"} and isinstance(item.get("content"), str):
            contents.append({
                "role": "model" if item["role"] == "assistant" else "user",
                "parts": [{"text": item["content"][:4000]}],
            })
    contents.append({"role": "user", "parts": [{"text": message}]})

    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.7,
        ),
    )
    return response.text


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
        details = str(error).replace(os.getenv("GEMINI_API_KEY", ""), "[hidden]")
        return jsonify({
            "error": f"حدث خطأ من Gemini: {type(error).__name__}: {details[:500]}"
        }), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
