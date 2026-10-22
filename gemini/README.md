# FLEX

مساعد ذكي بواجهة عربية متحركة يعمل باستخدام Gemini API.

## التشغيل محليًا

من داخل مجلد `gemini`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:GEMINI_API_KEY="ضع-مفتاح-Gemini-هنا"
python app.py
```

افتح بعد ذلك `http://127.0.0.1:5000`.

يمكن الحصول على مفتاح Gemini من Google AI Studio:
`https://aistudio.google.com/app/apikey`

## النشر المجاني على Render

1. ارفع المشروع إلى مستودع GitHub، ويجب أن يحتوي المستودع على مجلد `gemini` وملف `render.yaml`.
2. افتح Render واختر **New > Blueprint**.
3. اربط مستودع GitHub الخاص بالمشروع.
4. سيقرأ Render ملف `render.yaml` ويجهز خدمة `flex-ai`.
5. أضف قيمة `GEMINI_API_KEY` عندما يطلبها Render.
6. انتظر انتهاء البناء، ثم انسخ رابط الموقع وأرسله لأصدقائك.

الخطة المجانية تعطي رابطًا عامًا دائمًا، لكن الخدمة قد تتوقف مؤقتًا عند عدم الاستخدام، وقد يكون أول فتح بعدها أبطأ قليلًا.

لا تضع مفتاح Gemini داخل HTML أو JavaScript أو مستودع GitHub. ضعه فقط في متغيرات البيئة على جهازك أو Render.