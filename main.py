import streamlit as st
import time
import uuid
from datetime import datetime
from api.auth import authenticate_google, get_auth_status
from api.tasks import fetch_todays_tasks, complete_task
from api.sheets import append_task_record
from core.timer import TaskTimer
from core.estimator import fetch_past_tasks_from_sheet, estimate_task_duration

# ページ設定
st.set_page_config(
    page_title="Task Logger",
    page_icon="⏱️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

def render_auth_section():
    """設定/認証セクションのUI"""
    if get_auth_status():
        st.success("Google アカウントに接続済みです")
    else:
        st.warning("Google アカウントへのログインが必要です")
        if st.button("Googleアカウントで認証する", type="primary"):
            with st.spinner("ブラウザで認証を行ってください..."):
                creds = authenticate_google()
                if creds:
                    st.success("認証に成功しました！ページをリロードします。")
                    st.rerun()
                    
    st.markdown("---")
    st.subheader("スプレッドシート設定")
    
    # セッションステートから読み込み
    current_sheet_id = st.session_state.get('spreadsheet_id', "")
    
    # ユーザー入力
    new_sheet_id = st.text_input("記録先のスプレッドシートID", value=current_sheet_id, help="スプレッドシートURLの /d/ から /edit の間の文字列です")
    
    # 入力内容が変わった場合の処理
    if new_sheet_id and new_sheet_id != current_sheet_id:
        st.session_state.spreadsheet_id = new_sheet_id
        st.success("スプレッドシートIDを保存しました。")
        with st.spinner("過去のタスク履歴を読み込んでいます..."):
            past_tasks = fetch_past_tasks_from_sheet(new_sheet_id)
            st.session_state.past_tasks = past_tasks
            if past_tasks:
                st.success(f"{len(past_tasks)}件の過去履歴を読み込みました。見込み時間の算出に使用します。")
            else:
                st.info("過去の記録が見つかりませんでした。")
                
    # 初期ロード済みでない場合はIDがあれば読み直す
    elif new_sheet_id and 'past_tasks' not in st.session_state:
        with st.spinner("過去のタスク履歴を読み込んでいます..."):
            past_tasks = fetch_past_tasks_from_sheet(new_sheet_id)
            st.session_state.past_tasks = past_tasks
            if past_tasks:
                st.success(f"{len(past_tasks)}件の過去履歴を読み込みました。見込み時間の算出に使用します。")
            else:
               st.info("過去の記録が見つかりませんでした。")

def main():
    st.title("⏱️ Task Logger")
    st.markdown("ワンタッチで操作できるタスク記録ツール")
    
    # 認証領域
    with st.expander("設定 / 認証", expanded=not get_auth_status()):
        render_auth_section()
    
    if not get_auth_status():
        st.info("上の設定を展開してGoogleアカウントで認証を行ってください。")
        return
        
    st.divider()
    
    # メイン領域
    st.header("新しいタスク")
    
    if 'active_tasks' not in st.session_state:
        st.session_state.active_tasks = []
    col1, col2 = st.columns([3, 1])
    with col1:
        col1_1, col1_2 = st.columns([4, 1])
        with col1_1:
            # Google Tasksからの取得 (毎秒のリロードを防ぐためキャッシュ)
            if 'google_tasks_list' not in st.session_state:
                with st.spinner("タスクを読み込み中..."):
                    st.session_state.google_tasks_list = fetch_todays_tasks()
                    
            tasks_list = st.session_state.google_tasks_list
                
            task_options = []
            if tasks_list:
                for t in tasks_list:
                    title = t.get('title', '無題のタスク')
                    task_id = t.get('id')
                    task_options.append(f"{title} (ID: {task_id})")
            else:
                task_options.append("(今日のタスクはありません)")
                
            task_options.append("その他(手入力)")
            
            selected_option = st.selectbox("タスクを選択 (Google Tasks)", task_options)
            
            # 実際に保存するタスク名とIDの抽出処理
            selected_task_name = selected_option
            selected_task_id = str(uuid.uuid4())
            is_google_task = False
            
            if "(ID: " in selected_option:
                parts = selected_option.split(" (ID: ")
                selected_task_name = parts[0]
                selected_task_id = parts[1].replace(")", "")
                is_google_task = True
                
            if selected_option == "その他(手入力)":
                selected_task_name = st.text_input("タスク名を入力してください")

        with col1_2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("↻ 更新", help="Tasksを再読込", use_container_width=True):
                with st.spinner("タスクを読み込み中..."):
                    st.session_state.google_tasks_list = fetch_todays_tasks()
                st.rerun()

    with col2:
        # 見た目のため少し下げる
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("追加", use_container_width=True):
            if not selected_task_name:
                st.error("タスク名を入力してください")
                st.stop()
                
            new_task = TaskTimer(
                task_id=selected_task_id,
                task_name=selected_task_name,
                is_google_task=is_google_task
            )
            st.session_state.active_tasks.append(new_task)
            st.rerun()
        
    st.markdown("---")
    st.header("進行中のタスク")
    
    if not st.session_state.active_tasks:
        st.info("現在進行中のタスクはありません。「追加」ボタンからタスクを開始してください。")
        return
        
    # 定期的に画面を更新してタイマーを進める
    st_autorefresh = st.empty()
    
    tasks_to_remove = set()
    
    for i, task in enumerate(st.session_state.active_tasks):
        with st.container(border=True):
            tc1, tc2, tc3 = st.columns([3, 2, 2])
            
            with tc1:
                st.subheader(task.task_name)
                
                # 見込み時間の計算と表示 (初期追加時のみ計算してキャッシュするなどの工夫も可能だが簡略化)
                if task.estimated_seconds is None:
                    # まだ計算されていなければ計算
                    past_tasks = st.session_state.get('past_tasks', [])
                    if past_tasks:
                        est = estimate_task_duration(task.task_name, past_tasks)
                        task.estimated_seconds = est
                    else:
                        task.estimated_seconds = -1 # 計算不可マーク
                
                if task.estimated_seconds and task.estimated_seconds > 0:
                    mins = int(task.estimated_seconds / 60)
                    st.caption(f"見込み時間: 約 {mins} 分 (過去の類似タスクから)")
                else:
                    st.caption("見込み時間: 未算出")
            
            with tc2:
                current_time = task.get_current_elapsed()
                st.markdown(f"### ⏱️ {task.format_time(current_time)}")
                
            with tc3:
                action_col1, action_col2 = st.columns(2)
                with action_col1:
                    if task.is_running:
                        if st.button("⏸ 一時停止", key=f"pause_{task.task_id}"):
                            task.pause()
                            st.rerun()
                    else:
                        if st.button("▶ 開始", key=f"start_{task.task_id}", type="primary"):
                            task.start()
                            st.rerun()
                with action_col2:
                    if st.button("✅ 記録して終了", key=f"finish_{task.task_id}"):
                        task.pause()
                        
                        sheet_id = st.session_state.get('spreadsheet_id', '')
                        if not sheet_id:
                            st.error("設定からスプレッドシートIDを入力してください。")
                        else:
                            # 1. スプレッドシートに記録
                            start_dt = datetime.fromtimestamp(task.start_time) if task.start_time else datetime.now()
                            formatted_duration = task.format_time(task.elapsed_seconds)
                            
                            with st.spinner("記録中..."):
                                success, msg = append_task_record(
                                    sheet_id, 
                                    task.task_name,
                                    formatted_duration,
                                    task.elapsed_seconds,
                                    start_dt
                                )
                                
                                if success:
                                    st.toast(f"{task.task_name} をスプレッドシートに記録しました！")
                                    # 2. Google Tasks側の更新処理
                                    if task.is_google_task:
                                        t_success, t_msg = complete_task(task.task_id)
                                        if t_success:
                                            st.toast("Google Tasks側も「完了」に更新しました。")
                                        else:
                                            st.warning(f"Google Tasksの更新に失敗しました: {t_msg}")
                                            
                                    tasks_to_remove.add(i)
                                else:
                                    st.error(f"記録に失敗しました: {msg}")
                        
    # 完了したタスクをリストから削除
    if tasks_to_remove:
        st.session_state.active_tasks = [t for i, t in enumerate(st.session_state.active_tasks) if i not in tasks_to_remove]
        st.rerun()
    
    # いずれかのタスクが実行中の場合は、1秒ごとに画面を再描画する
    if any(t.is_running for t in st.session_state.active_tasks):
        time.sleep(1)
        st.rerun()

if __name__ == '__main__':
    main()
