"""Controllers package"""
from flask import Blueprint

# 創建藍圖
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
user_bp = Blueprint('user', __name__, url_prefix='/api/users')

# 導入控制器以註冊路由
from app.controllers import AuthController
from app.controllers import UserController

__all__ = ['auth_bp', 'user_bp']
