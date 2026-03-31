"""
MiroFish Backend 启动入口
"""

import os
import sys

# 解决 Windows 控制台中文乱码问题：在所有导入之前设置 UTF-8 编码
if sys.platform == 'win32':
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.config import Config


def main():
    """主函数"""
    # 验证配置
    errors = Config.validate()
    if errors:
        print("配置错误:", flush=True)
        for err in errors:
            print(f"  - {err}", flush=True)
        print("\n请检查环境变量或 .env 文件中的配置", flush=True)
        sys.exit(1)

    # 创建应用
    app = create_app()

    # Railway 使用 PORT 环境变量，回退到 FLASK_PORT 或默认 5001
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', os.environ.get('FLASK_PORT', '5001')))
    debug = Config.DEBUG

    print(f">>> MiroFish starting on {host}:{port} (debug={debug})", flush=True)

    # 启动服务
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    main()
