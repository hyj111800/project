import requests

API_BASE = "https://graduation-project-smart-lighting-system-production.up.railway.app"

 
def get_music_status():
    """현재 음악 상태 조회"""
    resp = requests.get(f"{API_BASE}/music", timeout=5)
    return resp.json()

def play_music_api(mode="classic"):
    """음악 재생(서버에 명령)"""
    resp = requests.post(f"{API_BASE}/music/play", json={"mode": mode}, timeout=5)
    return resp.json()

def stop_music_api():
    """음악 정지"""
    resp = requests.post(f"{API_BASE}/music/stop", timeout=5)
    return resp.json()

def set_music_volume_api(volume=80):
    """음악 볼륨 변경"""
    resp = requests.post(f"{API_BASE}/music/volume", json={"volume": volume}, timeout=5)
    return resp.json()

 
def get_led_status():
    """현재 LED 상태 조회"""
    resp = requests.get(f"{API_BASE}/led", timeout=5)
    return resp.json()

def set_led_api(color="#FF00FF", brightness=70, status="on"):
    """LED 상태/컬러/밝기 변경"""
    payload = {
        "color": color,
        "brightness": brightness,
        "status": status
    }
    resp = requests.post(f"{API_BASE}/led", json=payload, timeout=5)
    return resp.json()

 
def get_alarm(alarm_id=None, status=None, time=None):
    """특정 알람(쿼리 파라미터로) 또는 전체 알람 조회"""
    params = {}
    if alarm_id is not None: params['id'] = alarm_id
    if status is not None: params['status'] = status
    if time is not None: params['time'] = time
    resp = requests.get(f"{API_BASE}/alarm", params=params, timeout=5)
    return resp.json()

def post_alarm(status="on", time="07:30"):
    """알람 추가"""
    payload = {
        "status": status,
        "time": time
    }
    resp = requests.post(f"{API_BASE}/alarm", json=payload, timeout=5)
    return resp.json()

def delete_alarm(alarm_id):
    """알람 삭제"""
    resp = requests.delete(f"{API_BASE}/alarm/{alarm_id}", timeout=5)
    return resp.status_code

 
def get_routines():
    """전체 루틴 조회"""
    resp = requests.get(f"{API_BASE}/routine", timeout=5)
    return resp.json()

def post_routine(name, time, enabled, actions):
    """루틴 추가"""
    payload = {
        "name": name,
        "time": time,
        "enabled": enabled,
        "actions": actions
    }
    resp = requests.post(f"{API_BASE}/routine", json=payload, timeout=5)
    return resp.json()

def delete_routine(routine_id):
    """루틴 삭제"""
    resp = requests.delete(f"{API_BASE}/routine/{routine_id}", timeout=5)
    return resp.status_code

 
def get_qr_export(routine_id):
    """루틴 QR 내보내기"""
    resp = requests.get(f"{API_BASE}/qr/export", params={"routine_id": routine_id}, timeout=5)
    return resp.json()

def post_qr_import(qr_data):
    """QR 데이터로 세팅값 이식"""
    resp = requests.post(f"{API_BASE}/qr/import", json=qr_data, timeout=5)
    return resp.json()

 
