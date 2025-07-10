import os
import socket
import platform
import datetime
from typing import List
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import shutil

app = FastAPI(title="本地文件传输服务", description="端到端文件传输服务")

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 桌面路径
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")

# 传输历史记录
transfer_history = []

def get_local_ip():
    """获取本机IP地址"""
    try:
        # 连接到一个远程地址来获取本机IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

def get_device_info():
    """获取设备信息"""
    return {
        "hostname": platform.node(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "ip": get_local_ip()
    }

def add_to_history(filename: str, size: int, client_ip: str):
    """添加传输记录到历史"""
    record = {
        "filename": filename,
        "size": size,
        "client_ip": client_ip,
        "timestamp": datetime.datetime.now().isoformat(),
        "id": len(transfer_history) + 1
    }
    transfer_history.append(record)

@app.get("/")
async def root():
    """根路径"""
    return {"message": "本地文件传输服务正在运行", "server_info": get_device_info()}

@app.get("/api/server-info")
async def get_server_info():
    """获取服务器信息"""
    return get_device_info()

@app.get("/api/history")
async def get_history():
    """获取传输历史记录"""
    return {"history": transfer_history}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文件"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        # 确保桌面目录存在
        os.makedirs(DESKTOP_PATH, exist_ok=True)
        
        # 文件保存路径
        file_path = os.path.join(DESKTOP_PATH, file.filename)
        
        # 如果文件已存在，添加时间戳
        if os.path.exists(file_path):
            name, ext = os.path.splitext(file.filename)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(DESKTOP_PATH, f"{name}_{timestamp}{ext}")
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 获取文件大小
        file_size = os.path.getsize(file_path)
        
        # 添加到历史记录
        add_to_history(os.path.basename(file_path), file_size, "未知")
        
        return JSONResponse(content={
            "success": True,
            "message": f"文件 {os.path.basename(file_path)} 已成功保存到桌面",
            "filename": os.path.basename(file_path),
            "size": file_size,
            "path": file_path
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@app.post("/api/upload-multiple")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    """上传多个文件"""
    results = []
    
    for file in files:
        try:
            if not file.filename:
                continue
                
            # 确保桌面目录存在
            os.makedirs(DESKTOP_PATH, exist_ok=True)
            
            # 文件保存路径
            file_path = os.path.join(DESKTOP_PATH, file.filename)
            
            # 如果文件已存在，添加时间戳
            if os.path.exists(file_path):
                name, ext = os.path.splitext(file.filename)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = os.path.join(DESKTOP_PATH, f"{name}_{timestamp}{ext}")
            
            # 保存文件
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            # 添加到历史记录
            add_to_history(os.path.basename(file_path), file_size, "未知")
            
            results.append({
                "success": True,
                "filename": os.path.basename(file_path),
                "size": file_size
            })
            
        except Exception as e:
            results.append({
                "success": False,
                "filename": file.filename,
                "error": str(e)
            })
    
    return JSONResponse(content={"results": results})

@app.delete("/api/history/{item_id}")
async def delete_history_item(item_id: int):
    """删除历史记录项"""
    global transfer_history
    transfer_history = [item for item in transfer_history if item["id"] != item_id]
    return {"message": "历史记录已删除"}

@app.delete("/api/history")
async def clear_history():
    """清空历史记录"""
    global transfer_history
    transfer_history = []
    return {"message": "历史记录已清空"}

if __name__ == "__main__":
    local_ip = get_local_ip()
    port = 8000
    
    print(f"🚀 服务器启动成功!")
    print(f"📱 本地访问地址: http://localhost:{port}")
    print(f"🌐 网络访问地址: http://{local_ip}:{port}")
    print(f"💻 设备名称: {platform.node()}")
    print(f"📁 文件将保存到: {DESKTOP_PATH}")
    print(f"🔗 其他设备请访问: http://{local_ip}:{port}")
    
    uvicorn.run(app, host="0.0.0.0", port=port)