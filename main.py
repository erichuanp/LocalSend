# 创建一个完整的文件传输服务
import os
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import json
import time
from pathlib import Path
import cgi
import tempfile
import shutil

# 获取桌面路径
def get_desktop_path():
    """获取桌面路径"""
    home = Path.home()
    desktop_paths = [
        home / "Desktop",
        home / "桌面", 
    ]
    
    for path in desktop_paths:
        if path.exists():
            return str(path)
    
    # 如果找不到桌面，使用用户主目录
    return str(home)

# 获取本机IP地址
def get_local_ip():
    """获取本机局域网IP地址"""
    try:
        # 连接到一个远程地址来获取本机IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# 获取设备名称
def get_device_name():
    """获取设备名称"""
    try:
        return socket.gethostname()
    except:
        return "Unknown Device"

# 全局变量存储传输历史
transfer_history = []

class FileTransferHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """处理GET请求"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            # 获取客户端IP
            client_ip = self.client_address[0]
            
            html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文件传输服务</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .device-info {{
            background: rgba(255,255,255,0.2);
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
        }}
        
        .drop-zone {{
            border: 3px dashed #4facfe;
            border-radius: 15px;
            padding: 60px 20px;
            text-align: center;
            margin: 30px;
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        
        .drop-zone:hover, .drop-zone.dragover {{
            border-color: #00f2fe;
            background: rgba(79, 172, 254, 0.1);
            transform: scale(1.02);
        }}
        
        .drop-zone i {{
            font-size: 4em;
            color: #4facfe;
            margin-bottom: 20px;
        }}
        
        .drop-zone h3 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 1.5em;
        }}
        
        .drop-zone p {{
            color: #666;
            font-size: 1.1em;
        }}
        
        .history {{
            padding: 30px;
            border-top: 1px solid #eee;
        }}
        
        .history h3 {{
            color: #333;
            margin-bottom: 20px;
            font-size: 1.3em;
        }}
        
        .history-item {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            border-left: 4px solid #4facfe;
        }}
        
        .progress-bar {{
            width: 100%;
            height: 6px;
            background: #eee;
            border-radius: 3px;
            margin: 20px 0;
            overflow: hidden;
            display: none;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #4facfe, #00f2fe);
            width: 0%;
            transition: width 0.3s ease;
        }}
        
        .status {{
            text-align: center;
            padding: 15px;
            margin: 20px 30px;
            border-radius: 8px;
            display: none;
        }}
        
        .status.success {{
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }}
        
        .status.error {{
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }}
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><i class="fas fa-cloud-upload-alt"></i> 文件传输服务</h1>
            <div class="device-info">
                <p><strong>设备名称:</strong> {get_device_name()}</p>
                <p><strong>您的IP:</strong> {client_ip}</p>
                <p><strong>服务器IP:</strong> {get_local_ip()}</p>
            </div>
        </div>
        
        <div class="drop-zone" id="dropZone">
            <i class="fas fa-cloud-upload-alt"></i>
            <h3>拖拽文件或文件夹到这里</h3>
            <p>支持多文件同时传输，文件将自动保存到对方桌面</p>
            <input type="file" id="fileInput" multiple style="display: none;" webkitdirectory>
            <input type="file" id="fileInputSingle" multiple style="display: none;">
        </div>
        
        <div class="progress-bar" id="progressBar">
            <div class="progress-fill" id="progressFill"></div>
        </div>
        
        <div class="status" id="status"></div>
        
        <div class="history">
            <h3><i class="fas fa-history"></i> 传输历史</h3>
            <div id="historyList">
                <p style="color: #666; text-align: center;">暂无传输记录</p>
            </div>
        </div>
    </div>

    <script>
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const fileInputSingle = document.getElementById('fileInputSingle');
        const progressBar = document.getElementById('progressBar');
        const progressFill = document.getElementById('progressFill');
        const status = document.getElementById('status');
        const historyList = document.getElementById('historyList');

        // 防止默认拖拽行为
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {{
            dropZone.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        }});

        function preventDefaults(e) {{
            e.preventDefault();
            e.stopPropagation();
        }}

        // 拖拽效果
        ['dragenter', 'dragover'].forEach(eventName => {{
            dropZone.addEventListener(eventName, highlight, false);
        }});

        ['dragleave', 'drop'].forEach(eventName => {{
            dropZone.addEventListener(eventName, unhighlight, false);
        }});

        function highlight(e) {{
            dropZone.classList.add('dragover');
        }}

        function unhighlight(e) {{
            dropZone.classList.remove('dragover');
        }}

        // 处理文件拖拽
        dropZone.addEventListener('drop', handleDrop, false);
        dropZone.addEventListener('click', () => {{
            fileInputSingle.click();
        }});

        fileInputSingle.addEventListener('change', (e) => {{
            handleFiles(e.target.files);
        }});

        function handleDrop(e) {{
            const dt = e.dataTransfer;
            const files = dt.files;
            handleFiles(files);
        }}

        function handleFiles(files) {{
            if (files.length === 0) return;
            
            showStatus('正在上传文件...', 'info');
            progressBar.style.display = 'block';
            
            const formData = new FormData();
            for (let i = 0; i < files.length; i++) {{
                formData.append('files', files[i]);
            }}

            const xhr = new XMLHttpRequest();
            
            xhr.upload.addEventListener('progress', (e) => {{
                if (e.lengthComputable) {{
                    const percentComplete = (e.loaded / e.total) * 100;
                    progressFill.style.width = percentComplete + '%';
                }}
            }});

            xhr.addEventListener('load', () => {{
                progressBar.style.display = 'none';
                if (xhr.status === 200) {{
                    showStatus('文件上传成功！', 'success');
                    updateHistory();
                }} else {{
                    showStatus('上传失败，请重试', 'error');
                }}
            }});

            xhr.addEventListener('error', () => {{
                progressBar.style.display = 'none';
                showStatus('上传出错，请检查网络连接', 'error');
            }});

            xhr.open('POST', '/upload');
            xhr.send(formData);
        }}

        function showStatus(message, type) {{
            status.textContent = message;
            status.className = 'status ' + type;
            status.style.display = 'block';
            
            setTimeout(() => {{
                status.style.display = 'none';
            }}, 3000);
        }}

        function updateHistory() {{
            fetch('/history')
                .then(response => response.json())
                .then(data => {{
                    if (data.length === 0) {{
                        historyList.innerHTML = '<p style="color: #666; text-align: center;">暂无传输记录</p>';
                    }} else {{
                        historyList.innerHTML = data.map(item => 
                            `<div class="history-item">
                                <strong>${{item.filename}}</strong> 
                                <span style="color: #666; float: right;">${{item.timestamp}}</span>
                            </div>`
                        ).join('');
                    }}
                }});
        }}

        // 页面加载时更新历史记录
        updateHistory();
        
        // 每5秒更新一次历史记录
        setInterval(updateHistory, 5000);
    </script>
</body>
</html>
            """
            
            self.wfile.write(html_content.encode('utf-8'))
            
        elif self.path == '/history':
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(transfer_history, ensure_ascii=False).encode('utf-8'))
            
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        """处理POST请求（文件上传）"""
        if self.path == '/upload':
            try:
                # 解析multipart/form-data
                content_type = self.headers.get('Content-Type')
                if not content_type or not content_type.startswith('multipart/form-data'):
                    self.send_response(400)
                    self.end_headers()
                    return

                # 创建临时目录
                temp_dir = tempfile.mkdtemp()
                
                try:
                    # 解析上传的文件
                    form = cgi.FieldStorage(
                        fp=self.rfile,
                        headers=self.headers,
                        environ={
                            'REQUEST_METHOD': 'POST',
                            'CONTENT_TYPE': content_type,
                        }
                    )

                    desktop_path = get_desktop_path()
                    client_ip = self.client_address[0]
                    
                    uploaded_files = []
                    
                    if 'files' in form:
                        files = form['files']
                        if not isinstance(files, list):
                            files = [files]
                        
                        for file_item in files:
                            if file_item.filename:
                                # 安全的文件名处理
                                safe_filename = os.path.basename(file_item.filename)
                                if not safe_filename:
                                    continue
                                
                                # 目标文件路径
                                target_path = os.path.join(desktop_path, safe_filename)
                                
                                # 如果文件已存在，添加数字后缀
                                counter = 1
                                original_target = target_path
                                while os.path.exists(target_path):
                                    name, ext = os.path.splitext(original_target)
                                    target_path = f"{name}({counter}){ext}"
                                    counter += 1
                                
                                # 保存文件
                                with open(target_path, 'wb') as f:
                                    f.write(file_item.file.read())
                                
                                uploaded_files.append(safe_filename)
                                
                                # 添加到传输历史
                                transfer_history.append({
                                    'filename': safe_filename,
                                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                                    'from_ip': client_ip,
                                    'size': os.path.getsize(target_path)
                                })
                    
                    # 保持历史记录在合理数量内
                    if len(transfer_history) > 50:
                        transfer_history[:] = transfer_history[-50:]
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    
                    response = {
                        'status': 'success',
                        'message': f'成功上传 {len(uploaded_files)} 个文件',
                        'files': uploaded_files
                    }
                    self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                    
                finally:
                    # 清理临时目录
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    
            except Exception as e:
                print(f"上传错误: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                response = {
                    'status': 'error',
                    'message': f'上传失败: {str(e)}'
                }
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

def start_server(port=8888):
    """启动文件传输服务器"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, FileTransferHandler)
    
    local_ip = get_local_ip()
    device_name = get_device_name()
    desktop_path = get_desktop_path()
    
    print("=" * 60)
    print("🚀 文件传输服务已启动!")
    print("=" * 60)
    print(f"📱 设备名称: {device_name}")
    print(f"🌐 服务器地址: http://{local_ip}:{port}")
    print(f"📁 文件保存位置: {desktop_path}")
    print("=" * 60)
    print("📋 使用说明:")
    print("1. 在其他设备的浏览器中打开上述地址")
    print("2. 将文件或文件夹拖拽到网页中的上传区域")
    print("3. 文件将自动保存到本机桌面")
    print("4. 按 Ctrl+C 停止服务")
    print("=" * 60)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 服务已停止")
        httpd.server_close()

if __name__ == "__main__":
    # 可以修改端口号
    PORT = 8888
    start_server(PORT)