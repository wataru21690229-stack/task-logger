from googleapiclient.discovery import build
from api.auth import authenticate_google
from datetime import datetime, timedelta, timezone

def get_tasks_service():
    """Tasks APIサービスオブジェクトを取得する"""
    creds = authenticate_google()
    if not creds:
        return None
    try:
        service = build('tasks', 'v1', credentials=creds)
        return service
    except Exception as e:
        print(f"Error building tasks service: {e}")
        return None

def fetch_todays_tasks():
    """
    デフォルトのタスクリスト（@default）から、期日が今日以降、
    または期日が設定されていない未完了のタスクを取得する。
    """
    service = get_tasks_service()
    if not service:
        return []

    try:
        # まずはタスクを取得（最大100件）
        results = service.tasks().list(tasklist='@default', showCompleted=False, maxResults=100).execute()
        items = results.get('items', [])

        if not items:
            return []

        todays_tasks = []
        for task in items:
            # すべての未完了タスクを取得する (期限でフィルタしない)
            todays_tasks.append(task)
            
        return todays_tasks

    except Exception as e:
        print(f"Error fetching tasks: {e}")
        return []

def complete_task(task_id: str):
    """指定したタスクを完了状態にする"""
    service = get_tasks_service()
    if not service:
        return False, "Google認証エラー"
        
    try:
        # まずタスクを取得
        task = service.tasks().get(tasklist='@default', task=task_id).execute()
        # ステータスを完了に変更
        task['status'] = 'completed'
        # 更新
        updated_task = service.tasks().update(tasklist='@default', task=task_id, body=task).execute()
        return True, "完了にしました"
    except Exception as e:
        print(f"Error completing task: {e}")
        return False, f"エラー: {e}"

if __name__ == '__main__':
    # 動作確認用
    print("Fetching today's tasks...")
    tasks = fetch_todays_tasks()
    if tasks:
        print(f"Found {len(tasks)} tasks:")
        for t in tasks:
            due = t.get('due', 'No Due Date')[:10]
            print(f"- [{due}] {t.get('title')}")
    else:
        print("No tasks found or error occurred.")
