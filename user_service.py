from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# 配置 MySQL 数据库连接，增加连接池配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/tcs'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 连接池大小
app.config['SQLALCHEMY_POOL_SIZE'] = 20
# 连接池中空闲连接的超时时间（秒）
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30
# 连接池达到最大连接数后，新连接的等待时间（秒）
app.config['SQLALCHEMY_POOL_RECYCLE'] = -1
# 连接池达到最大连接数后，允许的额外连接数
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 20

db = SQLAlchemy(app)


# 定义用户模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


# 定义游戏历史记录模型
class GameHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    #user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    username = db.Column(db.String(255), nullable=True)
    start_time = db.Column(db.String(255), nullable=True)
    end_time = db.Column(db.String(255), nullable=True)
    score = db.Column(db.String(255), nullable=True)
    duration = db.Column(db.String(255), nullable=True)


# 初始化数据库
try:
    with app.app_context():
        db.create_all()
except SQLAlchemyError as e:
    logging.error(f"数据库初始化失败: {e}")
    raise


# 注册服务
@app.route('/register', methods=['GET'])
def register():
    username = request.args.get('username')
    password = request.args.get('password')

    print("username:", username)
    print("password:", password)

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    new_user = User(username=username, password=password)
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except IntegrityError as e:
        db.session.rollback()
        print(f"注册时发生完整性错误: {e}")
        return jsonify({"message": "Username already exists"}), 409
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"注册时发生数据库错误: {e}")
        return jsonify({"message": "Database error occurred during registration"}), 500


# 密码验证服务
@app.route('/verify', methods=['GET'])
def verify():
    username = request.args.get('username')
    password = request.args.get('password')

    logging.debug(f"Received verification request for username: {username}, password: {password}")

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    try:
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            return jsonify({"message": "Password verified successfully"}), 200
        else:
            return jsonify({"message": "Invalid username or password"}), 401
    except SQLAlchemyError as e:
        logging.error(f"验证时发生数据库错误: {e}")
        return jsonify({"message": "Database error occurred during verification"}), 500


# 记录游戏历史记录
@app.route('/game_history', methods=['GET'])
def game_history():
    user_id = request.args.get('user_id')
    username = request.args.get('username')
    start_time_str = request.args.get('start_time',"未记录")
    end_time_str = request.args.get('end_time',"未记录")
    score_str = request.args.get('score')

    print("user_id:",user_id)
    print("username:",username)
    print("start_time_str:",start_time_str)
    print("end_time_str:",end_time_str)
    print("score_str:",score_str)

    new_history = GameHistory(
        username=username,
        start_time=start_time_str,
        end_time=end_time_str,
        score=score_str,
        duration=""
    )

    try:
        db.session.add(new_history)
        db.session.commit()
        return jsonify({"message": "Game history recorded successfully"}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"记录游戏历史记录时发生数据库错误: {e}")
        return jsonify({"message": "Database error occurred while recording game history"}), 500


# 获取用户游戏历史记录
@app.route('/get_game_history', methods=['GET'])
def get_game_history():
    username = request.args.get('username')
    try:
        histories = GameHistory.query.filter_by(username=username).all()
        history_list = []
        for history in histories:
            history_dict = {
                "username": history.username,
                "start_time": history.start_time,
                "end_time": history.end_time,
                "score": history.score,
                "duration": str(history.duration)
            }
            history_list.append(history_dict)
        return jsonify(history_list), 200
    except SQLAlchemyError as e:
        logging.error(f"获取游戏历史记录时发生数据库错误: {e}")
        return jsonify({"message": "Database error occurred while getting game history"}), 500


if __name__ == '__main__':
    try:
        app.run(debug=True)
    except Exception as e:
        logging.error(f"应用启动失败: {e}")
