from flask import Blueprint, request, jsonify, render_template, current_app
from ..repositories.package_repository import PackageRepository
from ..repositories.icon_repository import IconRepository
import os
from datetime import datetime
# from androguard.core.bytecodes import apk
import plistlib
import zipfile
import time
import base64
from app.utils.package_utils import (
    check_apk_architecture,
    extract_info_plist,
    getappname_by_packagename,
    get_ip_and_port
)
from app.utils.oss_utils import (delete_oss_file,restore_oss_file,upload_to_oss,get_download_url,createplist)

from app.utils.auth import  token_required

import hashlib

package_bp = Blueprint('package', __name__, url_prefix='/api/packages')

@package_bp.route('/ip', methods=['GET'])
def get_ip_endpoint():
    """
    获取服务器IP和端口
    ---
    tags:
      - 系统信息
    responses:
      200:
        description: 成功返回服务器地址
        schema:
          type: string
          example: "127.0.0.1:5000"
    """
    return get_ip_and_port()

@package_bp.route('/', methods=['POST'])
def create_package():
    """
    创建软件包记录
    ---
    tags:
      - 软件包管理
    consumes:
      - application/json
    parameters:
      - in: body
        name: package
        description: 软件包信息
        required: true
        schema:
          type: object
          required:
            - version
            - name
            - size
            - system
            - package_name
            - oss_key
          properties:
            appname:
              type: string
              description: 应用名称
            version:
              type: string
              description: 版本号
            name:
              type: string
              description: 文件名
            size:
              type: integer
              description: 文件大小(字节)
            system:
              type: string
              description: 系统类型(android/ios)
            comment:
              type: string
              description: 备注信息
            ar:
              type: string
              description: 架构类型
              default: "x64"
            package_name:
              type: string
              description: 包名
            oss_key:
              type: string
              description: OSS存储键
    responses:
      201:
        description: 创建成功
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Package created successfully"
      400:
        description: 无效请求
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Missing required fields"
      500:
        description: 服务器错误
    """
    # if request.method == 'OPTIONS':
    #     # 返回CORS预检响应
    #     response = jsonify({'status': 'preflight'})
    #     response.headers.add('Access-Control-Allow-Origin', '*')
    #     response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    #     return response
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
            
        package_info = request.get_json()

        icon_data = package_info['icon']
        icon_id = None

        if icon_data:
          icon_name = hashlib.md5(icon_data.encode()).hexdigest()
          # print(icon_data)
          # print(icon_name)

          if IconRepository.get_id_by_name(icon_name):
            icon_id = IconRepository.get_id_by_name(icon_name)
          else:
            os.makedirs('temp', exist_ok=True)
            temp_file = f'temp/{icon_name}.png'
            
            # 保存为临时文件
            base64_to_png(icon_data, temp_file)
            
            # 上传到OSS
            oss_url = upload_to_oss(temp_file,f'package_icons/{icon_name}.png')

            icon = {'name':icon_name,'url':oss_url}
            icon_id = IconRepository.create(icon).id
            # 清理临时文件
            os.remove(temp_file)
        
        # 检查必填字段
        required_fields = ['version', 'name', 'size', 'system', 'package_name','oss_key']
        missing_fields = [field for field in required_fields if field not in package_info]
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
        
        package_data = {
            'appname': package_info.get('appname', ''),
            'version': package_info['version'],
            'name': package_info['name'],
            'size': package_info['size'],
            'system': package_info['system'],
            'create_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'comment': package_info.get('comment', ''),
            'ar': package_info.get('ar', 'x64'),
            'status': 0,
            'package_name': package_info['package_name'] ,
            'oss_key': package_info['oss_key'],
            'icon_id': icon_id
        }

        if package_info['system'] == 'ios':
            apptitles = ["学测学生端","学测教师端","学测家长端"]
            createplist(
              package_info['oss_key'], 
              package_info['package_name'], 
              package_info['version'], 
              apptitles[int(package_info['appname'])])

        PackageRepository.create(package_data)
        
        return jsonify({'message': 'Package created successfully'}), 201

    except Exception as e:
        current_app.logger.error(f"Create package error: {str(e)}")
        return jsonify({'error': str(e)}), 500



@package_bp.route('/<int:package_id>', methods=['PUT'])
def update_package(package_id):
    """
    更新软件包信息（描述或名称）
    ---
    tags:
      - 软件包管理
    parameters:
      - name: package_id
        in: path
        type: integer
        required: true
        description: 软件包ID
      - in: body
        name: body
        schema:
          type: object
          properties:
            comment:
              type: string
              description: 更新后的描述（可选）
            name:
              type: string
              description: 更新后的名称（可选）
    responses:
      200:
        description: 更新成功
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Package updated successfully"
      400:
        description: 无效请求（未提供任何可更新字段）
    """
    data = request.get_json()
    if not data or not any(key in data for key in ['comment', 'name']):
        return jsonify({'error': '必须提供 comment 或 name 至少一个字段'}), 400

    # 动态更新提供的字段
    update_data = {}
    if 'comment' in data:
        update_data['comment'] = data['comment']
    if 'name' in data:
        update_data['name'] = data['name']


    PackageRepository.update_package_info(
        package_id=package_id,
        **update_data
    )
    
    return jsonify({'message': 'Package updated successfully'})

@package_bp.route('/<int:package_id>', methods=['DELETE'])
def delete_package(package_id):
    """
    删除软件包记录及对应的OSS文件
    ---
    tags:
      - 软件包管理
    parameters:
      - name: package_id
        in: path
        type: integer
        required: true
        description: 软件包ID
    responses:
      200:
        description: 删除成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Deleted successfully"
      404:
        description: 软件包不存在
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: "Package not found"
      500:
        description: 删除失败
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: "Delete failed: OSS deletion error"
    """
    try:
        # 1. 先获取包信息（包含OSS key）
        package = PackageRepository.get(package_id)
        if not package:
            return jsonify({
                "success": False,
                "message": "Package not found"
            }), 404
        
        # 2. 先删除OSS文件
        oss_success = delete_oss_file(package.oss_key)
        if not oss_success:
            raise Exception("Failed to delete OSS file")
        
        # 3. 再删除数据库记录
        db_success = PackageRepository.delete(package_id)
        if not db_success:
            raise Exception("Failed to delete database record")
            
        return jsonify({
            "success": True,
            "message": "Deleted successfully"
        }), 200
        
    except Exception as e:
        # 失败后尝试回滚
        try:
            if 'Failed to delete OSS file' in str(e):
                # OSS删除失败，无需处理数据库
                pass
            elif 'Failed to delete database record' in str(e):
                # 数据库删除失败，尝试恢复OSS文件
                if 'oss_success' in locals() and oss_success:
                    restore_oss_file(package.oss_key)
        except Exception as rollback_error:
            logging.error(f"回滚失败: {str(rollback_error)}")
            
        return jsonify({
            "success": False,
            "message": f"Delete failed: {str(e)}"
        }), 500

@package_bp.route('/<int:package_id>', methods=['GET'])
def get_package_by_id(package_id):
    """
    获取指定ID的软件包详情
    ---
    tags:
      - 软件包管理
    parameters:
      - name: package_id
        in: path
        type: integer
        required: true
        description: 软件包ID
    responses:
      200:
        description: 软件包详情
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            package:
              $ref: '#/definitions/Package'
      404:
        description: 软件包不存在
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: "Package not found"
      500:
        description: 服务器错误
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: "Internal server error"
    """
    try:
        # 1. 从数据库获取软件包
        print("@@@@@",package_id)
        package = PackageRepository.get(package_id)

        # print(package)
        
        if not package:
            return jsonify({
                'success': False,
                'message': f'Package with ID {package_id} not found'
            }), 404
        
        # 2. 生成下载URL（如果有OSS存储）
        download_url = None
        # print(package.oss_key)
        if package.oss_key:
            try:
                rst = get_download_url(package.oss_key)
                download_url = rst['url']
                # print(rst,download_url)
            except Exception as e:
                current_app.logger.error(f"Failed to generate download URL: {str(e)}")
        
        plist_url = None

        if package.system == 'ios':
            plist_url = f"itms-services://?action=download-manifest&url=https://oss.superrabbithero.xyz/packages/plists/{package.oss_key[9:-4]}.plist"
        
        # 3. 构造响应数据
        package_data = {
            'id': package.id,
            'name': package.name,
            'appname':package.appname,
            'package_name': package.package_name,
            'version': package.version,
            'size': package.size,
            'system': package.system,
            'ar': package.ar,
            'create_time': package.create_time.isoformat() if package.create_time else None,
            'comment': package.comment,
            'download_url': download_url,
            'icon_url': package.icon.url,
            'plist_url': plist_url
        }
        
        return jsonify({
            'success': True,
            'package': package_data
        })
    except Exception as e:
        current_app.logger.error(f"Error getting package {package_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500
    

@package_bp.route('/versions', methods=['GET'])
def get_version_list():
    """
    获取版本列表
    ---
    tags:
      - 软件包查询
    parameters:
      - name: appname
        in: query
        type: string
        required: true
        description: 应用名称
      - name: system
        in: query
        type: string
        description: 系统类型(android/ios)
    responses:
      200:
        description: 版本列表
        schema:
          type: object
          properties:
            versions:
              type: array
              items:
                type: string
                example: "1.0.0"
    """
    appname = request.args.get('appname', 'default')
    system = request.args.get('system', None)
    
    versions = PackageRepository.get_versions(
        appname=appname,
        system=system if system != 'all' else None
    )
    
    return jsonify({'versions': versions})

@package_bp.route('/search', methods=['GET'])
@token_required
def search_packages():
    """
    分页搜索软件包
    ---
    tags:
      - 软件包查询
    parameters:
      - name: appname
        in: query
        type: string
        required: true
      - name: system
        in: query
        type: string
      - name: version
        in: query
        type: string
      - name: ar
        in: query
        type: string
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 10
    responses:
      200:
        description: 分页结果
        schema:
          type: object
          properties:
            packages:
              type: array
              items:
                $ref: '#/definitions/Package'
            total:
              type: integer
              example: 100
            pages:
              type: integer
              example: 10
      400:
        description: 参数错误
    """
    try:
        params = {
            'appname': request.args.get('appname', 'default'),
            'system': request.args.get('system'),
            'version': request.args.get('version'),
            'ar': request.args.get('ar'),
            'page': int(request.args.get('page', 1)),
            'per_page': int(request.args.get('per_page', 10))
        }
        
        pagination = PackageRepository.get_paginated_packages(**params)
        
        return jsonify({
            'packages': [p.to_dict() for p in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@package_bp.route('/download', methods=['GET'])
def generate_download_link():
    """
    生成下载链接
    ---
    tags:
      - 下载管理
    parameters:
      - name: filename
        in: query
        type: string
        required: true
        description: 文件名
    responses:
      200:
        description: 下载链接
        schema:
          type: object
          properties:
            link:
              type: string
              example: "http://example.com/static/app/test.apk"
      400:
        description: 缺少文件名
    """
    filename = request.args.get("filename")
    if not filename:
        return jsonify({'error': 'Filename required'}), 400
    
    base_url = f"http://{get_ip_and_port()}/static/app"
    
    if filename.endswith(".ipa"):
        plist_name = filename.replace('.ipa', '.plist')
        return jsonify({
            'link': f"itms-services://?action=download-manifest&url={base_url}/{plist_name}"
        })
    
    return jsonify({'link': f"{base_url}/{filename}"})





def base64_to_png(base64_data, output_path):
    """
    将Base64数据保存为PNG文件
    :param base64_data: 纯Base64字符串（不含data:image/png;base64,前缀）
    :param output_path: 输出文件路径
    """
    # 移除可能的Base64前缀
    if ";base64," in base64_data:
        base64_data = base64_data.split(";base64,")[1]
    
    # 解码并保存文件
    with open(output_path, "wb") as f:
        f.write(base64.b64decode(base64_data))

