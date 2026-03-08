from difflib import SequenceMatcher
from typing import List, Optional
from api.sheets import get_sheets_service

def calculate_similarity(a: str, b: str) -> float:
    """2つの文字列の類似度 (0.0 ~ 1.0) を計算する。"""
    if not a or not b:
        return 0.0
    # 簡単な正規化（空白を取り除くなど）
    norm_a = a.replace(" ", "").replace("　", "").lower()
    norm_b = b.replace(" ", "").replace("　", "").lower()
    return SequenceMatcher(None, norm_a, norm_b).ratio()

def fetch_past_tasks_from_sheet(spreadsheet_id: str) -> List[dict]:
    """
    スプレッドシートから過去の記録を取得する。
    フォーマット: [日時, タスク名, 所要時間(文字列), 所要時間(秒)] 
    と仮定し、戻り値はタスク名と所要時間(秒)のリスト。
    """
    service = get_sheets_service()
    if not service or not spreadsheet_id:
        return []
        
    try:
        # A列からD列まで取得
        range_name = 'A:D'
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        
        past_tasks = []
        # 1行目はヘッダーかもしれないが、念の為全て処理し、秒数が数値化できるものを抽出
        for row in values:
            if len(row) >= 4:
                task_name = row[1]
                try:
                    duration_sec = float(row[3])
                    past_tasks.append({
                        'name': task_name,
                        'duration_sec': duration_sec
                    })
                except ValueError:
                    pass # ヘッダー行や数値でない行はスキップ
                    
        return past_tasks
        
    except Exception as e:
        print(f"Error fetching past tasks: {e}")
        return []

def estimate_task_duration(target_task_name: str, past_tasks: List[dict], similarity_threshold: float = 0.5) -> Optional[float]:
    """
    過去のタスク履歴から、対象タスク名に類似したタスクを検索し、
    所要時間の平均（または見込み時間）を算出する。
    """
    if not target_task_name or not past_tasks:
        return None
        
    similar_task_durations = []
    
    for pt in past_tasks:
        past_name = pt.get('name', '')
        sim = calculate_similarity(target_task_name, past_name)
        if sim >= similarity_threshold:
            similar_task_durations.append(pt.get('duration_sec', 0.0))
            
    if not similar_task_durations:
        return None
        
    # 類似タスクの平均所要時間を返す
    return sum(similar_task_durations) / len(similar_task_durations)
