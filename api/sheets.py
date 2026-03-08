from googleapiclient.discovery import build
from api.auth import authenticate_google
from datetime import datetime
from typing import Optional

def get_sheets_service():
    """Sheets APIサービスオブジェクトを取得する"""
    creds = authenticate_google()
    if not creds:
        return None
    try:
        service = build('sheets', 'v4', credentials=creds)
        return service
    except Exception as e:
        print(f"Error building sheets service: {e}")
        return None

def append_task_record(spreadsheet_id: str, task_name: str, duration_str: str, duration_sec: float, start_time: Optional[datetime] = None):
    """
    指定したスプレッドシートにタスクの記録を追記する。
    シート名が指定されていない場合は、最初のシート（Sheet1など）に追記される。
    
    フォーマット:
    [日時 (YYYY/MM/DD HH:MM), タスク名, 所要時間(文字列), 所要時間(秒)]
    """
    service = get_sheets_service()
    if not service:
        return False, "Googleアカウントの認証が完了していません。"

    try:
        # 記録する日時
        dt = start_time if start_time else datetime.now()
        date_str = dt.strftime("%Y/%m/%d %H:%M")

        # 追記する行のデータ
        values = [
            [date_str, task_name, duration_str, round(duration_sec, 1)]
        ]
        body = {
            'values': values
        }
        
        # 値を入力（ユーザーが入力したように解釈させる USER_ENTERED）
        # 'シート1' などの特定シート名にするのが安全だが、汎用的に 'A:D' のように範囲指定して追記させる
        range_name = 'A:D'
        
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        
        return True, result.get('updates', {}).get('updatedRange', '')
        
    except Exception as e:
        error_msg = str(e)
        if "HttpError 404" in error_msg:
             return False, "スプレッドシートが見つかりません。URL（ID）が正しいか確認してください。"
        elif "HttpError 403" in error_msg:
             return False, "スプレッドシートへのアクセス権がありません。"
        return False, f"エラーが発生しました: {error_msg}"
