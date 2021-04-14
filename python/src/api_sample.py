"""
共通処理のサンプルコードです。
DB接続アリ版。ない処理書くときはその辺抜いてください。
"""
import json
import os
import traceback
from typing import List, Dict

from aws_xray_sdk.core import patch_all, xray_recorder
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import scoped_session

import common.common_func as common
from common.custom_logger import CustomLogger
from db.models import UserModel
from db.setup import get_sess_container, session_scope

# region コンテナ起動時に1度だけ動く初期処理
# 環境変数取得
USER = os.environ["RDS_USERNAME"]
PASSWORD = os.environ["RDS_PASSWORD"]
HOST = os.environ["RDS_HOSTNAME"]
PORT = int(os.environ["RDS_PORT"])
DB_NAME = os.environ["RDS_DB_NAME"]

# AWS X-Rayのパッチを適用
patch_all()

# ログフォーマット設定
logger = CustomLogger(os.environ["LOG_LEVEL"])


# endregion


@xray_recorder.capture("handler")
def handler(event, context):
    try:
        # region 初期処理
        # 関数名取得
        func_name = context.function_name
        # ロガーのセットアップ
        logger.set_default_value(func_name)
        # 開始ログ出力
        logger.start()

        # jwtトークンからCognitoのIDを抽出
        user_id = common.extract_cognito_id(event["headers"]["Authorization"])

        # 起動パラメータとユーザーIDをログ
        body: Dict = json.loads(event["body"])
        logger.api_request_contents_log(body, user_id)

        # DB接続セッション管理オブジェクトの生成
        sess_cont = get_sess_container(host=HOST, port=PORT, user=USER, pwd=PASSWORD, db=DB_NAME, client=func_name)
        # endregion

        # region メイン処理
        response = center(body, sess_cont)
        # endregion

        # region 終了処理
        # 終了ログ
        logger.end()

        # 返却
        return response
        # endregion

    except Exception as e:
        # region 例外処理
        # terminalやCloudWatch Logsで見やすいログ
        print(traceback.format_exc())

        # システム共通形式のログ
        logger.common_error(e.args[0], extra=traceback.format_exc())

        # 例外処理時のレスポンス作成
        response = common.common_error_response()

        # 返却
        return response
        # endregion


def center(body: Dict, sess_cont: scoped_session) -> Dict:
    """
    メイン処理
    @param body: リクエストボディ
    @type body: Dict
    @param sess_cont: セッション管理オブジェクト
    @type sess_cont: scoped_session
    @return: APIとしてのレスポンス
    @rtype: Dict
    """
    try:
        # DB操作の例
        # DBとのセッションを取得
        with session_scope(sess_cont) as session:

            # ユーザー作ってインサート
            user = UserModel(user_name="イイヅカ", mail_address="minazukitombo", authority=1, create_user=1,
                             update_user=1)
            session.add(user)

            # m_userから全件取得
            users: List[UserModel] = session.query(UserModel).all()
            for user in users:
                print(vars(users))
                print(user.user_name)

            # with句抜けるときに勝手にcommitしたりrollbackするので気にしなくてよし
        return {}

    except IntegrityError as e:
        # 一意制約エラー時
        print("一意制約例外")
        print(e)
        logger.common_error(e.args[0], extra=traceback.format_exc())
        return {}

    # except "更新失敗のエラー" as e:
    #     # 更新失敗時の処理はここに記載
