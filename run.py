from app import create_app

app = create_app()  # 确保创建应用实例

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)