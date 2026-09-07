import hashlib
import hmac
import json
import re
import time
from functools import wraps
from uuid import UUID, uuid4

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app import db
from models import ShuffleRoom, ShuffleParticipant

team_shuffle = Blueprint("team_shuffle", __name__)
TIERS = {"iron", "bronze", "silver", "gold", "platinum",
		 "diamond", "ascendant", "immortal", "radiant"}


class Problem(Exception):
	def __init__(self, message, status=400, code="invalid_request"):
		self.message, self.status, self.code = message, status, code


def endpoint(fn):
	@wraps(fn)
	def wrapped(*args, **kwargs):
		try:
			result = fn(*args, **kwargs)
			db.session.commit()
			return jsonify(result)
		except Problem as error:
			db.session.rollback()
			return jsonify(message=error.message, code=error.code), error.status
		except SQLAlchemyError:
			db.session.rollback()
			current_app.logger.exception("チーム分けAPIのDB処理に失敗しました")
			return jsonify(message="保存処理に失敗しました。再試行してください。",
						   code="database_error"), 503
		except Exception:
			db.session.rollback()
			raise
	return wrapped


@team_shuffle.after_request
def no_cache(response):
	response.headers["Cache-Control"] = "no-store"
	return response


def uid(value):
	try:
		parsed = UUID(value)
		if parsed.version != 4 or str(parsed) != value:
			raise ValueError()
		return value
	except (ValueError, TypeError, AttributeError):
		raise Problem("IDが不正です。")


def token_hash(value):
	if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
		raise Problem("本人確認情報が不正です。", 401, "unauthorized")
	return hashlib.sha256(value.encode()).hexdigest()


def bearer():
	# CGI等で標準ヘッダーが渡らない場合も、同じBearer秘密キーを検証する。
	headers = [value for value in (
		request.headers.get("Authorization"),
		request.headers.get("X-Team-Shuffle-Authorization"),
		request.environ.get("REDIRECT_HTTP_AUTHORIZATION"),
	) if value is not None]
	if not headers or any(not value.startswith("Bearer ") for value in headers):
		raise Problem("認証が必要です。", 401, "unauthorized")
	identities = [token_hash(value[7:]) for value in headers]
	if any(not hmac.compare_digest(identities[0], value) for value in identities[1:]):
		raise Problem("認証情報が一致しません。", 401, "unauthorized")
	return identities[0]


def body():
	data = request.get_json(silent=True)
	if not isinstance(data, dict):
		raise Problem("JSONオブジェクトを送信してください。")
	return data


def load_room(room_id, organizer=False):
	uid(room_id)
	# 同じ募集の読み書きを直列化する。SQLiteでも更新前に書込みロックを取得。
	db.session.execute(
		update(ShuffleRoom).where(ShuffleRoom.id == room_id)
		.values(revision=ShuffleRoom.revision)
		.execution_options(synchronize_session=False)
	)
	room = db.session.get(ShuffleRoom, room_id, populate_existing=True)
	if room is None:
		raise Problem("募集が見つかりません。", 404, "not_found")
	if organizer and not hmac.compare_digest(room.organizer_hash, bearer()):
		raise Problem("主催者の認証に失敗しました。", 403, "forbidden")
	return room


def room_dict(room):
	return room.to_dict()


def participants(room):
	return db.session.scalars(
		select(ShuffleParticipant)
		.where(ShuffleParticipant.room_id == room.id)
		.order_by(ShuffleParticipant.id)
	).all()


def participant_dict(p):
	return p.to_dict()


def snapshot(room):
	db.session.flush()
	return dict(room=room_dict(room),
				participants=[participant_dict(p) for p in participants(room)
							  if not p.removed])


def own_participant(room, identity):
	return db.session.scalar(select(ShuffleParticipant).where(
		ShuffleParticipant.room_id == room.id,
		ShuffleParticipant.token_hash == identity,
	))


def registration(room, p):
	info = room_dict(room)
	# 削除済みの本人トークンは、受付中なら新規参加と同じ状態として扱う。
	# 行とIDは再利用し、PUT時に復活させる。
	visible = None if p and p.removed else p
	reason = info["status"] if info["status"] != "open" else (
		"locked" if visible and visible.edit_locked else None)
	public_room = {key: info[key] for key in ("id", "status", "expiresAt")}
	return dict(room=public_room,
				participant=participant_dict(visible) if visible else None,
				editable=reason is None, reason=reason)


@team_shuffle.post("/rooms")
@endpoint
def create_room():
	data = body()
	room_id = uid(data.get("id"))
	identity = token_hash(data.get("organizerToken"))
	room = db.session.get(ShuffleRoom, room_id)
	if room is None:
		room = ShuffleRoom(id=room_id, organizer_hash=identity,
						   expires_at=int(time.time()) + 12 * 60 * 60)
		db.session.add(room)
		try:
			db.session.flush()
		except IntegrityError:
			# 同じ作成要求の並行再送。
			db.session.rollback()
	room = load_room(room_id)
	if not hmac.compare_digest(room.organizer_hash, identity):
		raise Problem("募集IDが使用されています。", 403, "forbidden")
	return snapshot(room)


@team_shuffle.get("/rooms/<room_id>")
@endpoint
def get_room(room_id):
	info = room_dict(load_room(room_id))
	return dict(room={key: info[key] for key in ("id", "status", "expiresAt")})


@team_shuffle.get("/rooms/<room_id>/participants")
@endpoint
def get_participants(room_id):
	return snapshot(load_room(room_id, organizer=True))


@team_shuffle.route("/rooms/<room_id>/registration", methods=["GET", "PUT"])
@endpoint
def register(room_id):
	identity = bearer()
	room = load_room(room_id)
	p = own_participant(room, identity)
	if request.method == "GET":
		return registration(room, p)
	state = registration(room, p)
	if not state["editable"]:
		messages = {
			"closed": "募集は終了しました。",
			"expired": "募集の有効期限が切れました。",
			"locked": "チーム分けが確定したため、情報を修正できません。",
		}
		raise Problem(messages[state["reason"]], 409, state["reason"])
	data = body()
	name, tier, div, vc = (data.get(key) for key in ("name", "tier", "div", "vc"))
	if (not isinstance(name, str) or not 1 <= len(name.strip()) <= 80
			or not isinstance(tier, str) or tier not in TIERS
			or type(div) is not int or div not in (1, 2, 3)
			or (tier == "radiant" and div != 1) or type(vc) is not bool):
		raise Problem("名前・ランク・ディビジョン・VC設定を確認してください。")
	values = dict(name=name.strip(), tier=tier, div=div, vc=vc)
	if p is None:
		p = ShuffleParticipant(id=str(uuid4()), room_id=room.id,
							   token_hash=identity, **values)
		db.session.add(p)
		room.revision += 1
	elif p.removed:
		for key, value in values.items():
			setattr(p, key, value)
		p.removed = False
		p.edit_locked = False
		p.version += 1
		room.revision += 1
	elif any(getattr(p, key) != value for key, value in values.items()):
		for key, value in values.items():
			setattr(p, key, value)
		p.version += 1
		room.revision += 1
	db.session.flush()
	return registration(room, p)


@team_shuffle.put("/rooms/<room_id>/edit-locks")
@endpoint
def edit_locks(room_id):
	room = load_room(room_id, organizer=True)
	data = body()
	operation_id = uid(data.get("operationId"))
	expected = data.get("expectedRevision")
	ids = data.get("participantIds")
	if (type(expected) is not int or expected < 0
			or not isinstance(ids, list) or not all(isinstance(v, str) for v in ids)
			or len(set(ids)) != len(ids)):
		raise Problem("編集ロックの指定が不正です。")
	for value in ids:
		uid(value)
	digest = hashlib.sha256(json.dumps(
		dict(expectedRevision=expected, participantIds=sorted(ids)),
		sort_keys=True, separators=(",", ":"),
	).encode()).hexdigest()
	if room.last_operation_id == operation_id:
		if room.last_operation_hash != digest:
			raise Problem("同じ操作IDを別の内容に使用できません。", 400)
		return snapshot(room)
	if room.revision != expected:
		raise Problem("参加者情報が更新されました。再取得してください。",
					  409, "revision_conflict")
	active = [p for p in participants(room) if not p.removed]
	selected = set(ids)
	if not selected.issubset({p.id for p in active}):
		raise Problem("参加者一覧が変更されています。", 409, "revision_conflict")
	for p in active:
		locked = p.id in selected
		if p.edit_locked != locked:
			p.edit_locked = locked
			p.version += 1
	room.revision += 1
	room.last_operation_id = operation_id
	room.last_operation_hash = digest
	return snapshot(room)


@team_shuffle.delete("/rooms/<room_id>/participants/<participant_id>")
@endpoint
def remove_participant(room_id, participant_id):
	room = load_room(room_id, organizer=True)
	uid(participant_id)
	p = db.session.get(ShuffleParticipant, participant_id)
	if p is None or p.room_id != room.id:
		raise Problem("参加者が見つかりません。", 404, "not_found")
	if not p.removed:
		p.removed = True
		p.version += 1
		room.revision += 1
	return snapshot(room)


@team_shuffle.post("/rooms/<room_id>/close")
@endpoint
def close_room(room_id):
	room = load_room(room_id, organizer=True)
	if not room.closed:
		room.closed = True
		room.revision += 1
	return snapshot(room)
