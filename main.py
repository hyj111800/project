# -*- coding: utf-8 -*-
import os
import json
import base64
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# ---- 설정
app = Flask(__name__)
CORS(app)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Missing DATABASE_URL environment variable")

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---- DB 모델 정의
class LED(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(10), nullable=False)
    color = db.Column(db.String(20), nullable=False)
    brightness = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Music(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(10), nullable=False)
    mode = db.Column(db.String(50), nullable=False)
    volume = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Alarm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(10), nullable=False)
    time = db.Column(db.String(10), nullable=False)  # "HH:MM"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Routine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    time = db.Column(db.String(10), nullable=False)  # "HH:MM"
    enabled = db.Column(db.Boolean, nullable=False, default=True)
    actions = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ---- 유틸 함수
def ok(data=None, code=200):
    if data is None:
        return jsonify({"ok": True}), code
    return jsonify(data), code

def bad(msg="Bad Request", code=400):
    return jsonify({"error": msg}), code

# ---- 초기화 엔드포인트
@app.route("/")
def home():
    return ok({"service": "Smart Lighting API", "time": datetime.utcnow().isoformat()+"Z"})

# ---- LED 제어
@app.route("/led", methods=["GET"])
def get_led():
    row = LED.query.order_by(LED.id.desc()).first()
    if not row:
        return ok({"status":"off","color":"#FFFFFF","brightness":100})
    return ok({"status": row.status, "color": row.color, "brightness": row.brightness})

@app.route("/led", methods=["POST"])
def post_led():
    data = request.get_json(force=True, silent=True) or {}
    status = data.get("status", "off")
    color = data.get("color", "#FFFFFF")
    brightness = data.get("brightness", 100)
    try:
        brightness = int(brightness)
    except:
        return bad("brightness must be integer 0-100")
    if brightness < 0 or brightness > 100:
        return bad("brightness must be 0-100")
    led = LED(status=status, color=color, brightness=brightness)
    db.session.add(led)
    db.session.commit()
    return ok({"status": status, "color": color, "brightness": brightness}, code=201)

# ---- Music 제어
@app.route("/music", methods=["GET"])
def get_music():
    row = Music.query.order_by(Music.id.desc()).first()
    if not row:
        return ok({"status":"off","mode":"classic","volume":80})
    return ok({"status": row.status, "mode": row.mode, "volume": row.volume})

@app.route("/music/play", methods=["POST"])
def play_music():
    data = request.get_json(force=True, silent=True) or {}
    mode = data.get("mode", "classic")
    row = Music(status="on", mode=mode, volume=80)
    db.session.add(row)
    db.session.commit()
    return ok({"status":"on","mode": mode, "volume": 80}, code=201)

@app.route("/music/stop", methods=["POST"])
def stop_music():
    last = Music.query.order_by(Music.id.desc()).first()
    mode = last.mode if last else "classic"
    row = Music(status="off", mode=mode, volume=(last.volume if last else 80))
    db.session.add(row)
    db.session.commit()
    return ok({"status":"off","mode": mode, "volume": (last.volume if last else 80)}, code=201)

@app.route("/music/volume", methods=["POST"])
def set_music_volume():
    data = request.get_json(force=True, silent=True) or {}
    try:
        volume = int(data.get("volume", 80))
    except:
        return bad("volume must be integer 0-100")
    if volume < 0 or volume > 100:
        return bad("volume must be 0-100")
    last = Music.query.order_by(Music.id.desc()).first()
    status = last.status if last else "off"
    mode = last.mode if last else "classic"
    row = Music(status=status, mode=mode, volume=volume)
    db.session.add(row)
    db.session.commit()
    return ok({"status": status, "mode": mode, "volume": volume}, code=201)

# ---- Alarm
@app.route("/alarm", methods=["GET"])
def get_alarm_list():
    args = request.args
    qry = Alarm.query
    if args.get("status") in ("on","off"):
        qry = qry.filter_by(status=args.get("status"))
    if args.get("time"):
        qry = qry.filter_by(time=args.get("time"))
    rows = qry.order_by(Alarm.id.desc()).all()
    result = [{"id": a.id, "status": a.status, "time": a.time} for a in rows]
    return ok(result)

@app.route("/alarm", methods=["POST"])
def post_alarm():
    data = request.get_json(force=True, silent=True) or {}
    status = data.get("status")
    time_ = data.get("time")
    if status not in ("on","off"):
        return bad("status must be 'on' or 'off'")
    if not time_ or len(time_)!=5:
        return bad("time must be 'HH:MM'")
    alarm = Alarm(status=status, time=time_)
    db.session.add(alarm)
    db.session.commit()
    return ok({"id": alarm.id, "status": alarm.status, "time": alarm.time}, code=201)

@app.route("/alarm/<int:alarm_id>", methods=["DELETE"])
def delete_alarm(alarm_id):
    Alarm.query.filter_by(id=alarm_id).delete()
    db.session.commit()
    return ok({"deleted": alarm_id})

# ---- Routine
@app.route("/routine", methods=["GET"])
def get_routines():
    rows = Routine.query.order_by(Routine.id.desc()).all()
    result = []
    for r in rows:
        result.append({
            "id": r.id,
            "name": r.name,
            "time": r.time,
            "enabled": r.enabled,
            "actions": r.actions
        })
    return ok(result)

@app.route("/routine", methods=["POST"])
def post_routine():
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name")
    time_ = data.get("time")
    enabled = bool(data.get("enabled", True))
    actions = data.get("actions", {})
    if not name or not time_:
        return bad("name and time are required")
    routine = Routine(name=name, time=time_, enabled=enabled, actions=actions)
    db.session.add(routine)
    db.session.commit()
    return ok({"id": routine.id, "name": routine.name, "time": routine.time, "enabled": routine.enabled, "actions": routine.actions}, code=201)

@app.route("/routine/<int:routine_id>", methods=["DELETE"])
def delete_routine(routine_id):
    Routine.query.filter_by(id=routine_id).delete()
    db.session.commit()
    return ok({"deleted": routine_id})

# ---- QR Export/Import
@app.route("/qr/export", methods=["POST"])
def qr_export():
    data = request.get_json(force=True, silent=True) or {}
    rid = data.get("routine_id")
    routine = Routine.query.filter_by(id=rid).first()
    if not routine:
        return bad("routine not found", code=404)
    payload = json.dumps({
        "id": routine.id,
        "name": routine.name,
        "time": routine.time,
        "enabled": routine.enabled,
        "actions": routine.actions
    }, ensure_ascii=False)
    qr_code = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")
    return ok({"qr_code": qr_code})

@app.route("/qr/import", methods=["POST"])
def qr_import():
    data = request.get_json(force=True, silent=True) or {}
    qr_code = data.get("qr_code")
    if not qr_code:
        return bad("qr_code required")
    try:
        decoded = base64.urlsafe_b64decode(qr_code.encode("ascii")).decode("utf-8")
        obj = json.loads(decoded)
        routine = Routine(
            name=obj.get("name","Imported"),
            time=obj.get("time","00:00"),
            enabled=obj.get("enabled", True),
            actions=obj.get("actions", {})
        )
        db.session.add(routine)
        db.session.commit()
        return ok({"imported": {"id": routine.id, "name": routine.name, "time": routine.time, "enabled": routine.enabled, "actions": routine.actions}}, code=201)
    except Exception as e:
        return bad(f"invalid qr_code: {str(e)}", code=400)

# ---- 서버 실행
if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    print(f"🚀 Flask Server Running on port {port}")

    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=port)
