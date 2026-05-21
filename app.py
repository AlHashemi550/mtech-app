#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import base64
import re
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# ========== مفتاح API الجديد ==========
# API KEY REMOVED FOR SECURITY
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
TEXT_MODEL = "llama-3.3-70b-versatile"

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

SYSTEM_PROMPT = """أنت مساعد ذكي متخصص في عالم البرمجة والتقنية. اسمك M•TECH.
قواعدك:
1. أجب باللغة العربية دائماً
2. كن دقيقاً ومفصلاً
3. عند تحليل الصور: حدد بدقة ما تراه
4. عند طلب روابط: قدم روابط حقيقية وصحيحة
5. استخدم Markdown في إجاباتك"""

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def format_response_with_links(text):
    url_pattern = r'(https?://[^\s<>"\']+)'
    return re.sub(url_pattern, r'<a href="\1" target="_blank" class="ai-link">\1</a>', text)

def call_groq_vision(base64_image, user_message=""):
    if not user_message:
        user_message = "حلل هذه الصورة بدقة تامة وأعطني كل المعلومات الممكنة عنها"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": VISION_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "text", "text": user_message},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]}
        ],
        "temperature": 0.7, "max_completion_tokens": 4096, "stream": False
    }
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"❌ خطأ: {str(e)}"

def call_groq_chat(messages):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": TEXT_MODEL,
        "messages": messages,
        "temperature": 0.7, "max_completion_tokens": 4096, "stream": False
    }
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"❌ خطأ: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/sections')
def sections():
    return render_template('sections.html')

@app.route('/analyze-image', methods=['POST'])
def analyze_image():
    if 'image' not in request.files:
        return jsonify({'error': 'لم يتم اختيار صورة'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'لم يتم اختيار صورة'}), 400
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"upload_{timestamp}_{file.filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    user_message = request.form.get('message', '')
    
    try:
        base64_image = encode_image_to_base64(filepath)
        result = call_groq_vision(base64_image, user_message)
        formatted = format_response_with_links(result)
        return jsonify({'success': True, 'result': formatted, 'raw_result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except:
            pass

@app.route('/chat-message', methods=['POST'])
def chat_message():
    data = request.get_json()
    messages = data.get('messages', [])
    if not messages:
        return jsonify({'error': 'لا توجد رسائل'}), 400
    if not any(m.get('role') == 'system' for m in messages):
        messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
    try:
        result = call_groq_chat(messages)
        formatted = format_response_with_links(result)
        return jsonify({'success': True, 'result': formatted, 'raw_result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 50)
    print(" 🚀 M•TECH - Smart AI Assistant")
    print("=" * 50)
    print(" 📱 افتح المتصفح على: http://127.0.0.1:5000")
    print("=" * 50)
    port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port, host='0.0.0.0', port=5000, debug=True)
