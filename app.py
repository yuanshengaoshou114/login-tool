import os
import uuid
import threading
import hashlib
import time
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from PIL import Image
import UnityPy
from UnityPy.enums import ClassIDType, TextureFormat

app = Flask(__name__)
app.secret_key = "secret"
PORT = int(os.environ.get('PORT', 5000))

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "输出文件"
UPLOAD_FOLDER = BASE_DIR / "临时上传"
LOGIN_TEMPLATE = BASE_DIR / "login"

OUTPUT_DIR.mkdir(exist_ok=True)
UPLOAD_FOLDER.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

TOKENS = {}
SHARED_KEY = "genshin_shared_key_2024"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def delayed_delete(file_path, delay_seconds=600):
    def delete():
        time.sleep(delay_seconds)
        try:
            if file_path.exists():
                file_path.unlink()
        except:
            pass
    threading.Thread(target=delete, daemon=True).start()

def generate_token(tg_user_id):
    token = hashlib.md5(f"{tg_user_id}{time.time()}{SHARED_KEY}".encode()).hexdigest()
    TOKENS[token] = {
        'user_id': tg_user_id,
        'expires': time.time() + 3600
    }
    return token

def check_token(token):
    if not token or token not in TOKENS:
        return None
    token_data = TOKENS[token]
    if time.time() > token_data['expires']:
        del TOKENS[token]
        return None
    return token_data['user_id']
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>碧蓝航线Login图替换</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            min-height: 100vh;
            background: url('https://tupian.genshinnb.shop/144387040_p0.jpg') no-repeat center center fixed;
            background-size: cover;
            font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
            padding: 20px;
            position: relative;
        }
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.3);
            z-index: 0;
        }
        .container {
            position: relative;
            z-index: 1;
            max-width: 450px;
            margin: 80px auto;
            background: rgba(255,255,255,0.95);
            border-radius: 24px;
            padding: 40px 35px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            backdrop-filter: blur(2px);
        }
        h1 {
            text-align: center;
            font-size: 26px;
            color: #1a2a6c;
            margin-bottom: 10px;
            font-weight: 600;
        }
        .hint {
            text-align: center;
            font-size: 12px;
            color: #27ae60;
            margin-bottom: 30px;
            background: #e8f5e9;
            padding: 8px;
            border-radius: 20px;
        }
        .file-label {
            display: block;
            padding: 14px;
            background: #f0f2f5;
            border: 2px dashed #bbb;
            border-radius: 40px;
            text-align: center;
            cursor: pointer;
            margin: 12px 0;
            transition: all 0.3s;
            font-size: 15px;
            color: #555;
        }
        .file-label:hover {
            border-color: #1a2a6c;
            background: #e8eef9;
        }
        .file-name {
            text-align: center;
            font-size: 12px;
            color: #666;
            margin-top: -5px;
            margin-bottom: 10px;
            word-break: break-all;
        }
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #1a2a6c, #b21f1f, #fdbb4d);
            background-size: 200% 200%;
            color: white;
            border: none;
            border-radius: 40px;
            cursor: pointer;
            font-weight: bold;
            font-size: 16px;
            margin-top: 20px;
            transition: all 0.3s;
        }
        button:hover {
            animation: gradientShift 1s ease infinite;
            transform: translateY(-2px);
        }
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        button:disabled {
            opacity: 0.6;
            transform: none;
            cursor: not-allowed;
        }
        .message {
            margin-top: 20px;
            padding: 12px;
            border-radius: 30px;
            display: none;
            text-align: center;
            font-size: 14px;
        }
        .success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .loading {
            text-align: center;
            margin-top: 20px;
            display: none;
        }
        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #1a2a6c;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .footer {
            text-align: center;
            margin-top: 25px;
            font-size: 11px;
            color: #999;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>碧蓝航线Login图替换</h1>
        <div class="hint">✅ 已通过TG频道验证 | 会话有效期1小时</div>
        
        <input type="file" id="image" accept="image/png,image/jpeg,image/jpg" style="display:none">
        <div class="file-label" onclick="document.getElementById('image').click()">
             点击选择图片 
        </div>
        <div class="file-name" id="fileName">未选择任何文件</div>
        
        <button onclick="upload()" id="submitBtn">开始替换</button>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p style="margin-top:10px">处理中，请稍候...</p>
        </div>
        <div class="message" id="message"></div>
        <div class="footer">替换后自动下载 | 文件10分钟后自动清理</div>
    </div>

    <script>
        let selectedFile = null;
        
        document.getElementById('image').addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                selectedFile = e.target.files[0];
                document.getElementById('fileName').innerText = '✅ ' + selectedFile.name;
            } else {
                selectedFile = null;
                document.getElementById('fileName').innerText = '未选择任何文件';
            }
        });
        
        async function upload() {
            if (!selectedFile) {
                showMsg('❌ 请选择图片文件', 'error');
                return;
            }
            
            const urlParams = new URLSearchParams(window.location.search);
            const token = urlParams.get('token');
            
            if (!token) {
                showMsg('❌ 验证失败，请重新获取链接', 'error');
                return;
            }
            
            const formData = new FormData();
            formData.append('image', selectedFile);
            
            document.getElementById('submitBtn').disabled = true;
            document.getElementById('loading').style.display = 'block';
            document.getElementById('message').style.display = 'none';
            
            try {
                const res = await fetch('/upload?token=' + token, { method: 'POST', body: formData });
                const data = await res.json();
                
                if (data.success) {
                    showMsg('✅ 替换成功！正在下载...', 'success');
                    const a = document.createElement('a');
                    a.href = data.download_url;
                    a.download = '';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    setTimeout(() => {
                        document.getElementById('image').value = '';
                        selectedFile = null;
                        document.getElementById('fileName').innerText = '未选择任何文件';
                    }, 1000);
                } else {
                    showMsg('❌ ' + data.message, 'error');
                }
            } catch(e) {
                showMsg('❌ 网络错误，请重试', 'error');
            } finally {
                document.getElementById('submitBtn').disabled = false;
                document.getElementById('loading').style.display = 'none';
            }
        }
        
        function showMsg(msg, type) {
            const el = document.getElementById('message');
            el.innerHTML = msg;
            el.className = 'message ' + type;
            el.style.display = 'block';
            setTimeout(() => {
                if (el.style.display === 'block') {
                    el.style.display = 'none';
                }
            }, 5000);
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    token = request.args.get('token')
    user_id = check_token(token)
    if not user_id:
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>访问被拒绝</title>
            <style>
                body {
                    min-height: 100vh;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    font-family: 'Microsoft YaHei', sans-serif;
                }
                .container {
                    background: white;
                    padding: 40px;
                    border-radius: 20px;
                    text-align: center;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    max-width: 400px;
                }
                h1 { color: #e74c3c; margin-bottom: 20px; }
                p { color: #666; margin-bottom: 15px; line-height: 1.6; }
                .btn {
                    display: inline-block;
                    margin-top: 20px;
                    padding: 12px 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 40px;
                    font-weight: bold;
                }
                .hint {
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 10px;
                    font-size: 14px;
                    color: #666;
                    margin-top: 20px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>⚠️ 访问被拒绝</h1>
                <p>此工具仅供频道成员使用</p>
                <p>请先关注频道，然后发送 <code style="background:#eee;padding:2px 6px;border-radius:4px">/login_tool</code> 获取访问链接</p>
                <div class="hint">
                    📢 频道链接：<a href="https://t.me/genshinnb114514" target="_blank">@genshinnb114514</a>
                </div>
            </div>
        </body>
        </html>
        ''', 403
    return HTML_TEMPLATE

@app.route('/api/get_token', methods=['POST'])
def get_token():
    data = request.get_json()
    tg_user_id = data.get('tg_user_id')
    key = data.get('key')
    
    if key != SHARED_KEY:
        return jsonify({'success': False, 'error': 'Invalid key'}), 401
    
    if not tg_user_id:
        return jsonify({'success': False, 'error': 'Missing user_id'}), 400
    
    token = generate_token(tg_user_id)
    return jsonify({
        'success': True,
        'token': token,
        'expires_in': 3600,
        'url': f'https://web-production-1b6b96.up.railway.app/?token={token}'
    })

@app.route('/upload', methods=['POST'])
def upload():
    token = request.args.get('token')
    user_id = check_token(token)
    
    if not user_id:
        return jsonify({'success': False, 'message': '验证失败或会话已过期，请重新获取链接'}), 401
    
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': '请选择图片'}), 400
    
    file = request.files['image']
    if not file or not file.filename or not allowed_file(file.filename):
        return jsonify({'success': False, 'message': '仅支持 PNG/JPG/JPEG 格式'}), 400
    
    img_id = uuid.uuid4().hex
    img_path = UPLOAD_FOLDER / f"{img_id}.png"
    file.save(str(img_path))
    
    if not LOGIN_TEMPLATE.exists():
        return jsonify({'success': False, 'message': '服务器资源文件缺失'}), 500
    
    env = UnityPy.load(str(LOGIN_TEMPLATE))
    
    with Image.open(img_path) as img:
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        w, h = img.size
        
        for obj in env.objects:
            if obj.type == ClassIDType.Texture2D:
                tex = obj.read()
                tex.set_image(img, TextureFormat.RGBA32)
                tex.save()
            elif obj.type == ClassIDType.Sprite:
                spr = obj.read()
                spr.m_Rect.width = float(w)
                spr.m_Rect.height = float(h)
                if hasattr(spr, "m_RD") and hasattr(spr.m_RD, "textureRect"):
                    spr.m_RD.textureRect.width = float(w)
                    spr.m_RD.textureRect.height = float(h)
                spr.save()
    
    out_filename = f"login_{img_id}"
    out_path = OUTPUT_DIR / out_filename
    with open(out_path, "wb") as f:
        if hasattr(env, 'file') and env.file is not None:
            f.write(env.file.save(packer="lz4"))
        elif hasattr(env, 'files') and env.files:
            first_file = next(iter(env.files.values()))
            f.write(first_file.save(packer="lz4"))
        else:
            raise Exception("保存失败")
    
    delayed_delete(img_path, 600)
    delayed_delete(out_path, 600)
    
    return jsonify({
        'success': True,
        'download_url': f'/download/{out_filename}?token={token}'
    })

@app.route('/download/<filename>')
def download(filename):
    token = request.args.get('token')
    user_id = check_token(token)
    
    if not user_id:
        return '验证失败或会话已过期', 401
    
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        return '文件已过期或不存在', 404
    return send_file(file_path, as_attachment=True, download_name='login')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
