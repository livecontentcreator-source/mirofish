"""
MiroFish Backend - Flask应用工厂
"""

import os
import warnings

# 抑制 multiprocessing resource_tracker 的警告（来自第三方库如 transformers）
# 需要在所有其他导入之前设置
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask, request, send_from_directory
from flask_cors import CORS

from .config import Config
from .utils.logger import setup_logger, get_logger

# 前端构建产物路径 (生产环境: frontend/dist 在项目根目录)
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), '../../frontend/dist')


def create_app(config_class=Config):
    """Flask应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 设置JSON编码：确保中文直接显示（而不是 \uXXXX 格式）
    # Flask >= 2.3 使用 app.json.ensure_ascii，旧版本使用 JSON_AS_ASCII 配置
    if hasattr(app, 'json') and hasattr(app.json, 'ensure_ascii'):
        app.json.ensure_ascii = False
    
    # 设置日志
    logger = setup_logger('mirofish')
    
    # 只在 reloader 子进程中打印启动信息（避免 debug 模式下打印两次）
    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    debug_mode = app.config.get('DEBUG', False)
    should_log_startup = not debug_mode or is_reloader_process
    
    if should_log_startup:
        logger.info("=" * 50)
        logger.info("MiroFish Backend 启动中...")
        logger.info("=" * 50)
    
    # 启用CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # 注册模拟进程清理函数（确保服务器关闭时终止所有模拟进程）
    from .services.simulation_runner import SimulationRunner
    SimulationRunner.register_cleanup()
    if should_log_startup:
        logger.info("已注册模拟进程清理函数")
    
    # 请求日志中间件
    @app.before_request
    def log_request():
        logger = get_logger('mirofish.request')
        logger.debug(f"请求: {request.method} {request.path}")
        if request.content_type and 'json' in request.content_type:
            logger.debug(f"请求体: {request.get_json(silent=True)}")
    
    @app.after_request
    def log_response(response):
        logger = get_logger('mirofish.request')
        logger.debug(f"响应: {response.status_code}")
        return response
    
    # 注册蓝图
    from .api import graph_bp, simulation_bp, report_bp
    app.register_blueprint(graph_bp, url_prefix='/api/graph')
    app.register_blueprint(simulation_bp, url_prefix='/api/simulation')
    app.register_blueprint(report_bp, url_prefix='/api/report')
    
    # 健康检查
    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'MiroFish Backend'}
    
    # ---- 生产环境：由 Flask 提供前端静态文件 ----
    frontend_dist_abs = os.path.abspath(FRONTEND_DIST)
    if os.path.isdir(frontend_dist_abs):
        if should_log_startup:
            logger.info(f"检测到前端构建产物，启用静态文件服务: {frontend_dist_abs}")

        @app.route('/', defaults={'path': ''})
        @app.route('/<path:path>')
        def serve_frontend(path):
            """
            为 Vue SPA 提供服务:
            - 如果请求的文件存在于 dist/ 中，直接返回
            - 否则返回 index.html（支持前端路由）
            """
            file_path = os.path.join(frontend_dist_abs, path)
            if path and os.path.isfile(file_path):
                return send_from_directory(frontend_dist_abs, path)
            return send_from_directory(frontend_dist_abs, 'index.html')
    else:
        if should_log_startup:
            logger.info("未检测到前端构建产物，仅提供 API 服务（开发模式）")
    
    if should_log_startup:
        logger.info("MiroFish Backend 启动完成")
    
    return app
