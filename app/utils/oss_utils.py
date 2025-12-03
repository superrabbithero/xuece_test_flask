from aliyunsdkcore.client import AcsClient
from aliyunsdksts.request.v20150401 import AssumeRoleRequest
from oss2.exceptions import OssError, NoSuchKey
import oss2 
from oss2 import Auth, Bucket, exceptions
from functools import lru_cache
from urllib.parse import urlparse

import logging
# from flask import jsonify
from datetime import datetime, timedelta
import json
from config import Config

class OSSOperationError(Exception):
    """自定义OSS操作异常"""
    pass

def get_bucket():
    """
    获取OSS Bucket实例
    :return: oss2.Bucket 实例
    """
    auth = Auth(
        Config.OSS_ACCESS_KEY_ID,
        Config.OSS_ACCESS_KEY_SECRET
    )

    endpoint = f"https://oss-{Config.OSS_REGION}.aliyuncs.com"
    print(f"OSS Endpoint: {endpoint}")  # 调试用

    bucket = Bucket(auth, endpoint, Config.OSS_BUCKET)

    # 测试连接
    bucket.get_bucket_info()
    print("OSS Bucket 连接成功")

    return bucket

def get_oss_client():
    """获取OSS客户端"""
    try:
        # 使用主账号AK创建客户端
        client = AcsClient(
            ak=Config.OSS_ACCESS_KEY_ID,
            secret=Config.OSS_ACCESS_KEY_SECRET,
            region_id=Config.OSS_REGION
        )
        return client
    except Exception as e:
        print(f"创建OSS客户端失败: {str(e)}")
        raise OSSOperationError(f"客户端创建失败: {str(e)}")
        
def generate_sts_token():
    """
    生成 OSS 临时上传凭证（STS Token）
    使用阿里云 SDK v3 风格改造
    """
    try:
        # 1. 初始化客户端（新版推荐使用 credential 链）
        client =  get_oss_client()

        # 2. 创建 AssumeRole 请求
        request = AssumeRoleRequest.AssumeRoleRequest()
        request.set_accept_format('json')  # 明确指定返回格式
        
        # 3. 设置角色参数
        request.set_RoleArn(Config.OSS_ROLE_ARN)
        request.set_RoleSessionName('vue3-upload-session')
        request.set_DurationSeconds(Config.OSS_TOKEN_EXPIRE)
        
        # 4. 设置精细化的权限策略(可以不设置策略)
        # policy = {
        #     "Version": "1",
        #     "Statement": [{
        #         "Effect": "Allow",
        #         "Action": ["oss:PutObject"],
        #         "Resource": [
        #             f"acs:oss:*:*:{Config.OSS_BUCKET}/packages/*",
        #             f"acs:oss:*:*:{Config.OSS_BUCKET}"  # 某些操作需要bucket级别权限
        #         ],
        #         "Condition": {
        #             "IpAddress": {"acs:SourceIp": Config.ALLOWED_IPS} if hasattr(Config, 'ALLOWED_IPS') else None
        #         }
        #     }]
        # }
        # request.set_Policy(json.dumps(policy))

        # 5. 发送请求并处理响应
        response = client.do_action_with_exception(request)
        response_data = json.loads(response.decode('utf-8'))
        
        credentials = response_data['Credentials']
        return {
            'status': 'success',
            'data': {
                'access_key_id': credentials['AccessKeyId'],
                'access_key_secret': credentials['AccessKeySecret'],
                'security_token': credentials['SecurityToken'],
                'expiration': credentials['Expiration'],
                'bucket': Config.OSS_BUCKET,
                'region': Config.OSS_REGION,
                'endpoint': f"https://{Config.OSS_BUCKET}.{Config.OSS_REGION}.aliyuncs.com"
            }
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'STS Token 生成失败: {str(e)}',
            'debug_info': {
                'role_arn': Config.OSS_ROLE_ARN,
                'region': Config.OSS_REGION,
                'bucket': Config.OSS_BUCKET
            }
        }

def delete_oss_file(oss_key):
    """
    删除OSS文件
    :param oss_key: 文件路径
    :raises: OSSOperationError
    :return: bool 是否成功
    """
    # print(oss_key)
    try:
        # print(f"开始创建bucket")
        bucket = get_bucket()

        info = bucket.get_bucket_info()
        # print(f"Bucket验证成功，创建时间: {info.creation_date}")

        result = bucket.delete_object(oss_key)
        return result.status == 204
    except NoSuchKey:
        logging.warning(f"文件不存在: {oss_key}")
        return True  # 文件不存在视为成功
    except OssError as e:
        logging.error(f"OSS删除失败: {str(e)}")
        raise OSSOperationError(f"OSS删除失败: {str(e)}")

def restore_oss_file(oss_key):
    """
    恢复OSS文件（需开启版本控制）
    :param oss_key: 文件路径
    :raises: OSSOperationError
    :return: bool 是否成功
    """
    try:
        bucket = get_bucket()
        result = bucket.restore_object(oss_key)
        return result.status == 202
    except OssError as e:
        logging.error(f"OSS恢复失败: {str(e)}")
        raise OSSOperationError(f"OSS恢复失败: {str(e)}")

def upload_to_oss(file_path, object_name=None):
    """
    上传文件到阿里云OSS
    :param file_path: 本地文件路径
    :param object_name: OSS上的目标路径（包含文件名），如果为None则自动生成
    :return: 文件在OSS的URL
    """
    
    # 初始化OSS客户端
    bucket = get_bucket()
    
    # 生成唯一文件名（如果未指定）
    if not object_name:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        object_name = f"images/{timestamp}.png"
    
    if Config.APP_ENV != 'production':
        object_name = f"test/{object_name}"
    # 上传文件
    with open(file_path, 'rb') as f:
        bucket.put_object(object_name, f)
    
    print("@@@@@@", object_name)

    # 返回可访问的URL
    return f"https://{Config.OSS_BUCKET}.oss-{Config.OSS_REGION}.aliyuncs.com/{object_name}"

def get_download_url(oss_key):
    bucket = get_bucket()

    expires = 3600  # 单位：秒
    # 生成原始签名URL（含OSS默认域名）
    original_url = bucket.sign_url('GET', oss_key, expires)
    
    # 解析原始URL，提取路径和查询参数
    parsed_url = urlparse(original_url)
    path_and_query = parsed_url.path + "?" + parsed_url.query
    
    # 替换为自定义域名（需确保已绑定到OSS Bucket）
    custom_domain = "oss.superrabbithero.xyz"  # 替换为你的自定义域名
    custom_url = f"https://{custom_domain}{path_and_query}"

    # print(url)
    
    return {
        'url': custom_url,
        'expires': (datetime.now() + timedelta(seconds=expires)).isoformat()
    }

def createplist(oss_key, bundle_id, version, apptitle):
    print("上传plist到OSS")
    
    filename = (oss_key[14:-4] + ".plist") if Config.APP_ENV != 'production' else (oss_key[9:-4] + ".plist")

    print(filename)
    
    # 生成plist内容
    content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>items</key>
        <array>
            <dict>
                <key>assets</key>
                <array>
                    <dict>
                        <key>kind</key>
                        <string>software-package</string>
                        <key>url</key>
                        <string>https://oss.superrabbithero.xyz/""" + oss_key + """</string>
                    </dict>
                    <dict>
                        <key>kind</key>
                        <string>full-size-image</string>
                        <key>needs-shine</key>
                        <true/>
                        <key>url</key>
                        <string>https://enterprise.cloudpay.com.cn/app/packages/iphone-2x.png</string>
                    </dict>
                </array>
                <key>metadata</key>
                    <dict>
                    <key>bundle-identifier</key>
                    <string>""" + bundle_id + """</string>
                    <key>bundle-version</key>
                    <string>""" + version + """</string>
                    <key>kind</key>
                    <string>software</string>
                    <key>title</key>
                    <string>""" + apptitle + """</string>
                </dict>
            </dict>
        </array>
</dict>
</plist>"""
    
    try:
        # 获取OSS bucket
        bucket = get_bucket()

        base_path = "test/" if Config.APP_ENV != 'production' else ""
        
        # 上传文件到OSS
        print(f"{base_path}packages/plists/{filename}")
        bucket.put_object(
            key = f"{base_path}packages/plists/{filename}",
            data=content,             # 文件内容
            headers={
                'Content-Type': 'application/x-plist'  # 设置正确的Content-Type
            }
        )
        
        print(f"成功上传plist文件到OSS: {filename}")
        return {'success': True, 'filename': filename}
        
    except Exception as e:
        print(f"上传plist到OSS失败: {str(e)}")
        return {'error': str(e)}