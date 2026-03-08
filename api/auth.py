import streamlit as st
import json
from google.oauth2 import service_account

def authenticate_google():
    """設定(Secrets)からGoogleの認証情報を読み込みます"""
    try:
        if "CREDENTIALS_JSON" in st.secrets:
            # SecretsからJSON文字列を読み込んで辞書形式に変換
            creds_info = json.loads(st.secrets["CREDENTIALS_JSON"])
            # サービスアカウントとして認証
            creds = service_account.Credentials.from_service_account_info(creds_info)
            return creds
        else:
            st.error("設定(Secrets)に CREDENTIALS_JSON が見つかりません。")
            return None
    except Exception as e:
        st.error(f"認証エラーが発生しました: {e}")
        return None

def get_auth_status():
    """認証設定が完了しているか確認します"""
    return "CREDENTIALS_JSON" in st.secrets
