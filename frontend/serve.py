"""
简单的静态文件服务器
用于本地开发测试前端页面
"""
import http.server
import socketserver
import os
from pathlib import Path

# 切换到web目录
web_dir = Path(__file__).parent / "web"
os.chdir(web_dir)

PORT = 3000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # 添加CORS头，允许跨域请求
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print("="*60)
        print(f"  前端服务器启动成功！")
        print("="*60)
        print(f"  访问: http://127.0.0.1:{PORT}")
        print(f"  目录: {web_dir}")
        print("="*60)
        print("  按 Ctrl+C 停止服务器")
        print("="*60)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务器已停止")


