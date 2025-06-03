import requests
from flask import current_app, Response
from functools import wraps
import json
import time

class APIError(Exception):
    """自定义 API 错误异常"""
    def __init__(self, message, status_code=None, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code or 400
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status_code'] = self.status_code
        return rv

def handle_api_errors(f):
    """处理 API 调用错误的装饰器"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"API request failed: {str(e)}")
            raise APIError(f"External API request failed: {str(e)}", status_code=503)
        except json.JSONDecodeError as e:
            current_app.logger.error(f"API response JSON decode failed: {str(e)}")
            raise APIError("Invalid API response format", status_code=502)
        except APIError as e:
            raise e
        except Exception as e:
            current_app.logger.error(f"Unexpected API error: {str(e)}")
            raise APIError("Unexpected API error", status_code=500)
    return wrapper

def make_api_request(method, url, **kwargs):
    """
    通用的 API 请求方法
    :param method: HTTP 方法 (get, post, put, delete)
    :param url: API 地址
    :param kwargs: requests 请求参数
    :return: 响应数据 (字典)
    """
    methods = {
        'get': requests.get,
        'post': requests.post,
        'put': requests.put,
        'delete': requests.delete,
    }
    
    if method not in methods:
        raise ValueError(f"Unsupported HTTP method: {method}")
    
    try:
        response = methods[method](url, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        raise APIError(f"HTTP error occurred: {http_err}", status_code=response.status_code)
    except Exception as err:
        raise APIError(f"Other error occurred: {err}")


base_path_dict = {
    "test1":"https://xuece-xqdsj-stagingtest1.unisolution.cn",
    "test2":"https://xuece-xqdsj-stagingtest1.unisolution.cn",
    "pro":"https://xuece-xqdsj-stagingtest1.unisolution.cn"
}
        
class XueceAPIs:

    def __init__(self, env):
        self.base_path = base_path_dict[env]
        self.headers = {
            'Authtoken': '',
            'Xc-App-User-Schoolid': '',
            'Content-Type': 'application/json'
        }


    @handle_api_errors
    def login(self, username, pwd):
        """获取登录信息"""
        url = f"{self.base_path}/api/usercenter/nnauth/user/login?username={username}&encryptpwd={pwd}&clienttype=BROWSER&clientversion=1.25.7&systemversion=chrome122.0.0.0"

        data = make_api_request('get', url)

        print(data)

        try:
            self.headers['Authtoken'] = data['data']['authtoken']
            self.headers['Xc-App-User-Schoolid'] = f"{data['data']['user']['schoolId']}"
        except KeyError as e:
            raise APIError(f"Missing expected field in response: {str(e)}")

        print("login:@@@@@@"+self.headers['Authtoken'])


    @handle_api_errors
    def get_answercard(self, card_type='exam' , paper_id='1'):

        print("get_answercard:@@@@@@"+self.headers['Authtoken'])
        url = f"{self.base_path}/api/examcenter/teacher/answercard/editinfo?exampaperId={paper_id}"
        if card_type == "classwork":
            url = f"{self.base_path}/api/classworkcenter/nnauth/claswork/answercardpreview?classworkId={paper_id}"

        return make_api_request('get', url, headers=self.headers)

