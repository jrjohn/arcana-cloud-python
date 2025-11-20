"""
WSGI 應用入口
用於生產環境部署
"""
import os
from app import create_app

# 從環境變數獲取配置
config_name = os.getenv('FLASK_ENV', 'production')

# 創建應用實例
app = create_app(config_name)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
