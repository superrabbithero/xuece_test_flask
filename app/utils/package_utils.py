# app/utils.py
import os
import zipfile
import logging
from functools import wraps
from typing import Optional, Tuple
from flask import current_app, request

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_errors(func):
    """统一错误处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            raise  # 抛出异常由上层处理
    return wrapper

@handle_errors
def check_apk_architecture(apk_path: str) -> str:
    """检测APK支持的CPU架构
    
    Args:
        apk_path: APK文件路径
        
    Returns:
        str: 架构描述 (x32/x64/x32、x64/未知)
    """
    arch = {"32bit": False, "64bit": False}
    
    with zipfile.ZipFile(apk_path, 'r') as zf:
        for file in zf.namelist():
            if 'lib/armeabi' in file:
                arch["32bit"] = True
            elif 'lib/arm64-v8a' in file:
                arch["64bit"] = True

    if arch["32bit"] and arch["64bit"]:
        return "x32、x64"
    elif arch["32bit"]:
        return "x32"
    elif arch["64bit"]:
        return "x64"
    return "未知"

@handle_errors
def extract_info_plist(ipa_path: str) -> Optional[str]:
    """从IPA包中提取Info.plist文件
    
    Args:
        ipa_path: IPA文件路径
        
    Returns:
        str: 提取的Info.plist文件路径
    """
    with zipfile.ZipFile(ipa_path, 'r') as zf:
        for f in zf.namelist():
            if f.count('/') == 2 and f.endswith('Info.plist'):
                extract_path = os.path.join(
                    current_app.config['UPLOAD_FOLDER'], 
                    os.path.basename(f)
                )
                zf.extract(f, current_app.config['UPLOAD_FOLDER'])
                return os.path.join(current_app.config['UPLOAD_FOLDER'], f)
    return None

@handle_errors
def getappname_by_packagename(package_name: str, default_appname: str) -> int:
    """根据包名映射应用分类ID
    
    Args:
        package_name: 应用程序包名
        default_appname: 默认分类
        
    Returns:
        int: 应用分类ID
    """
    package_mapping = {
        "cn.unisolution.onlineexam": 1,
        "com.uni.tchxueceapp": 1,
        "cn.unisolution.onlineexamstu": 0,
        "com.uni.stuxueceapp": 0
    }
    return package_mapping.get(package_name, default_appname)

@handle_errors
def get_ip_and_port() -> str:
    """获取当前服务的IP和端口
    
    Returns:
        str: IP:Port 格式的字符串
    """
    host_info = request.host.split(':')
    ip = host_info[0]
    port = host_info[1] if len(host_info) > 1 else '80'
    return f"{ip}:{port}"

# 高级工具函数
@handle_errors
def safe_file_remove(file_path: str) -> bool:
    """安全删除文件
    
    Args:
        file_path: 要删除的文件路径
        
    Returns:
        bool: 是否删除成功
    """
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

@handle_errors
def validate_file_type(filename: str, allowed_extensions: Tuple[str]) -> bool:
    """验证文件扩展名是否合法
    
    Args:
        filename: 文件名
        allowed_extensions: 允许的扩展名元组
        
    Returns:
        bool: 是否通过验证
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions
