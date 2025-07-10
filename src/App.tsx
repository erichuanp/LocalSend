import React, { useState, useEffect, useCallback } from 'react';
import { Upload, History, Monitor, Wifi, Check, X, Trash2, RefreshCw } from 'lucide-react';

interface ServerInfo {
  hostname: string;
  system: string;
  machine: string;
  processor: string;
  ip: string;
}

interface TransferHistoryItem {
  id: number;
  filename: string;
  size: number;
  client_ip: string;
  timestamp: string;
}

interface UploadResult {
  success: boolean;
  filename: string;
  size?: number;
  error?: string;
}

function App() {
  const [serverInfo, setServerInfo] = useState<ServerInfo | null>(null);
  const [history, setHistory] = useState<TransferHistoryItem[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState<UploadResult[]>([]);
  const [showResults, setShowResults] = useState(false);
  const [isOnline, setIsOnline] = useState(false);

  // 后端服务地址
  const API_BASE = 'http://localhost:8000';

  // 检查服务器连接状态
  const checkServerStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/server-info`);
      if (response.ok) {
        const data = await response.json();
        setServerInfo(data);
        setIsOnline(true);
      } else {
        setIsOnline(false);
      }
    } catch (error) {
      setIsOnline(false);
    }
  }, []);

  // 获取传输历史
  const fetchHistory = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/history`);
      if (response.ok) {
        const data = await response.json();
        setHistory(data.history);
      }
    } catch (error) {
      console.error('获取历史记录失败:', error);
    }
  }, []);

  // 初始化
  useEffect(() => {
    checkServerStatus();
    fetchHistory();
    
    // 定时检查服务器状态
    const interval = setInterval(checkServerStatus, 5000);
    
    return () => clearInterval(interval);
  }, [checkServerStatus, fetchHistory]);

  // 文件大小格式化
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 时间格式化
  const formatTime = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleString('zh-CN');
  };

  // 拖拽处理
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (!isOnline) {
      alert('服务器未连接，请检查后端服务是否启动');
      return;
    }

    const files = Array.from(e.dataTransfer.files);
    if (files.length === 0) return;

    await uploadFiles(files);
  };

  // 文件上传
  const uploadFiles = async (files: File[]) => {
    setIsUploading(true);
    setShowResults(false);
    const results: UploadResult[] = [];

    try {
      const formData = new FormData();
      files.forEach((file) => {
        formData.append('files', file);
      });

      const response = await fetch(`${API_BASE}/api/upload-multiple`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        results.push(...data.results);
      } else {
        results.push({
          success: false,
          filename: `${files.length}个文件`,
          error: '上传失败'
        });
      }
    } catch (error) {
      results.push({
        success: false,
        filename: `${files.length}个文件`,
        error: '网络错误'
      });
    }

    setUploadResults(results);
    setShowResults(true);
    setIsUploading(false);
    
    // 刷新历史记录
    fetchHistory();
    
    // 3秒后自动隐藏结果
    setTimeout(() => {
      setShowResults(false);
    }, 3000);
  };

  // 文件选择上传
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      uploadFiles(files);
    }
  };

  // 清空历史记录
  const clearHistory = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/history`, {
        method: 'DELETE',
      });
      if (response.ok) {
        setHistory([]);
      }
    } catch (error) {
      console.error('清空历史记录失败:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* 状态栏 */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Monitor className="w-6 h-6 text-blue-600" />
              <h1 className="text-xl font-bold text-gray-800">本地文件传输服务</h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className={`flex items-center space-x-2 px-3 py-1 rounded-full ${
                isOnline ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
              }`}>
                <div className={`w-2 h-2 rounded-full ${isOnline ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-sm font-medium">
                  {isOnline ? '服务在线' : '服务离线'}
                </span>
              </div>
              <button
                onClick={checkServerStatus}
                className="p-2 rounded-full hover:bg-gray-100 transition-colors"
                title="刷新状态"
              >
                <RefreshCw className="w-4 h-4 text-gray-600" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* 服务器信息 */}
        {serverInfo && (
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
              <Wifi className="w-5 h-5 mr-2 text-blue-600" />
              连接信息
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">设备名称</p>
                <p className="text-lg font-medium text-gray-900">{serverInfo.hostname}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">IP地址</p>
                <p className="text-lg font-medium text-blue-600">{serverInfo.ip}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">系统</p>
                <p className="text-lg font-medium text-gray-900">{serverInfo.system}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">架构</p>
                <p className="text-lg font-medium text-gray-900">{serverInfo.machine}</p>
              </div>
            </div>
          </div>
        )}

        {/* 文件上传区域 */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
            <Upload className="w-5 h-5 mr-2 text-blue-600" />
            文件上传
          </h2>
          
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-all duration-300 ${
              isDragging 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-300 hover:border-gray-400'
            } ${isUploading ? 'opacity-50' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            {isUploading ? (
              <div className="flex flex-col items-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
                <p className="text-lg text-gray-600">正在上传文件...</p>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                <Upload className="w-12 h-12 text-gray-400 mb-4" />
                <p className="text-lg text-gray-600 mb-2">
                  拖拽文件到这里或点击选择文件
                </p>
                <p className="text-sm text-gray-500 mb-4">
                  文件将自动保存到桌面
                </p>
                <input
                  type="file"
                  multiple
                  onChange={handleFileSelect}
                  className="hidden"
                  id="file-input"
                />
                <label
                  htmlFor="file-input"
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer"
                >
                  选择文件
                </label>
              </div>
            )}
          </div>

          {/* 上传结果 */}
          {showResults && uploadResults.length > 0 && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <h3 className="text-md font-medium text-gray-800 mb-2">上传结果</h3>
              <div className="space-y-2">
                {uploadResults.map((result, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-white rounded">
                    <div className="flex items-center space-x-2">
                      {result.success ? (
                        <Check className="w-4 h-4 text-green-600" />
                      ) : (
                        <X className="w-4 h-4 text-red-600" />
                      )}
                      <span className="text-sm text-gray-700">{result.filename}</span>
                    </div>
                    {result.success && result.size && (
                      <span className="text-sm text-gray-500">{formatFileSize(result.size)}</span>
                    )}
                    {!result.success && (
                      <span className="text-sm text-red-600">{result.error}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 传输历史 */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-800 flex items-center">
              <History className="w-5 h-5 mr-2 text-blue-600" />
              传输历史
            </h2>
            {history.length > 0 && (
              <button
                onClick={clearHistory}
                className="flex items-center space-x-1 px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded transition-colors"
              >
                <Trash2 className="w-4 h-4" />
                <span>清空</span>
              </button>
            )}
          </div>
          
          {history.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <History className="w-12 h-12 mx-auto mb-2 text-gray-300" />
              <p>暂无传输记录</p>
            </div>
          ) : (
            <div className="space-y-2">
              {history.slice().reverse().map((item) => (
                <div key={item.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{item.filename}</p>
                    <p className="text-sm text-gray-500">{formatTime(item.timestamp)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-700">{formatFileSize(item.size)}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;