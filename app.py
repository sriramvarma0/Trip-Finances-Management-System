import json
import os
import sqlite3
import uuid
from datetime import date, datetime

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data.db")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask(__name__, static_folder="static")
CORS(app)


@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def make_id():
    return uuid.uuid4().hex[:8]


def today_str():
    return date.today().isoformat()


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS trips (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            destination TEXT,
            created TEXT,
            is_current INTEGER DEFAULT 0
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS members (
            id TEXT PRIMARY KEY,
            trip_id TEXT NOT NULL,
            name TEXT NOT NULL,
            FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
        )
        """
    )

    expected_tx_columns = {
        "id",
        "trip_id",
        "type",
        "desc",
        "category",
        "amount",
        "payer",
        "receiver",
        "participants",
        "date",
        "reference",
    }
    existing_tx_columns = {
        row[1]
        for row in cur.execute("PRAGMA table_info(transactions)").fetchall()
    }
    
    if not existing_tx_columns:
        # Create new table if it doesn't exist
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                trip_id TEXT NOT NULL,
                type TEXT NOT NULL,
                desc TEXT NOT NULL,
                category TEXT,
                amount REAL NOT NULL,
                payer TEXT NOT NULL,
                receiver TEXT,
                participants TEXT,
                date TEXT,
                reference TEXT,
                FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
            )
            """
        )
    else:
        # Add missing columns to existing table
        missing_columns = expected_tx_columns - existing_tx_columns
        for col in missing_columns:
            if col == "reference":
                cur.execute("ALTER TABLE transactions ADD COLUMN reference TEXT")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS itinerary (
            trip_id TEXT PRIMARY KEY,
            data TEXT NOT NULL DEFAULT '[]',
            updated_at TEXT,
            FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
        )
        """
    )

    conn.commit()
    conn.close()


init_db()


def fetch_trip(conn, trip_id):
    cur = conn.cursor()
    trip = cur.execute(
        "SELECT id, name, destination, created, is_current FROM trips WHERE id = ?",
        (trip_id,),
    ).fetchone()
    if not trip:
        return None

    members = cur.execute(
        "SELECT id, trip_id, name FROM members WHERE trip_id = ? ORDER BY name ASC",
        (trip_id,),
    ).fetchall()

    txs = cur.execute(
        """
        SELECT id, trip_id, type, desc, category, amount, payer, receiver, participants, date, reference
        FROM transactions
        WHERE trip_id = ?
        ORDER BY date DESC, id DESC
        """,
        (trip_id,),
    ).fetchall()

    itinerary_row = cur.execute(
        "SELECT data FROM itinerary WHERE trip_id = ?",
        (trip_id,),
    ).fetchone()

    itinerary = []
    if itinerary_row and itinerary_row["data"]:
        try:
            parsed = json.loads(itinerary_row["data"])
            if isinstance(parsed, list):
                itinerary = parsed
        except json.JSONDecodeError:
            itinerary = []

    return {
        "trip": dict(trip),
        "members": [dict(m) for m in members],
        "transactions": [dict(t) for t in txs],
        "itinerary": itinerary,
    }


def normalize_name(name):
    return (name or "").strip().upper()


def parse_beneficiaries(value):
    if isinstance(value, list):
        return [normalize_name(v) for v in value if normalize_name(v)]
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return []
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [normalize_name(v) for v in parsed if normalize_name(v)]
        except json.JSONDecodeError:
            return [normalize_name(value)]
    return []


@app.route("/api/trips", methods=["GET"])
def list_trips():
    conn = get_db_connection()
    trips = conn.execute(
        "SELECT id, name, destination, created, is_current FROM trips ORDER BY created DESC, id DESC"
    ).fetchall()
    conn.close()
    return jsonify({"trips": [dict(t) for t in trips]})


@app.route("/api/trips", methods=["POST"])
def create_trip():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    destination = (payload.get("destination") or "").strip()

    if not name:
        return jsonify({"error": "Trip name is required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    existing = cur.execute("SELECT COUNT(*) AS count FROM trips").fetchone()["count"]
    trip_id = make_id()
    is_current = 1 if existing == 0 else 0

    cur.execute(
        "INSERT INTO trips (id, name, destination, created, is_current) VALUES (?, ?, ?, ?, ?)",
        (trip_id, name, destination, today_str(), is_current),
    )
    conn.commit()

    trip = cur.execute(
        "SELECT id, name, destination, created, is_current FROM trips WHERE id = ?",
        (trip_id,),
    ).fetchone()
    conn.close()

    return jsonify({"trip": dict(trip)}), 201


@app.route("/api/trips/<trip_id>", methods=["GET"])
def get_trip(trip_id):
    conn = get_db_connection()
    data = fetch_trip(conn, trip_id)
    conn.close()

    if not data:
        return jsonify({"error": "Trip not found"}), 404

    return jsonify(data)


@app.route("/api/trips/<trip_id>/itinerary", methods=["GET"])
def get_itinerary(trip_id):
    conn = get_db_connection()
    trip = conn.execute("SELECT id FROM trips WHERE id = ?", (trip_id,)).fetchone()
    if not trip:
        conn.close()
        return jsonify({"error": "Trip not found"}), 404

    row = conn.execute("SELECT data FROM itinerary WHERE trip_id = ?", (trip_id,)).fetchone()
    conn.close()

    itinerary = []
    if row and row["data"]:
        try:
            parsed = json.loads(row["data"])
            if isinstance(parsed, list):
                itinerary = parsed
        except json.JSONDecodeError:
            itinerary = []

    return jsonify({"itinerary": itinerary})


@app.route("/api/trips/<trip_id>/itinerary", methods=["PUT"])
def save_itinerary(trip_id):
    payload = request.get_json(silent=True)
    if isinstance(payload, list):
        itinerary = payload
    elif isinstance(payload, dict):
        itinerary = payload.get("itinerary") or []
    else:
        itinerary = []

    if not isinstance(itinerary, list):
        return jsonify({"error": "Itinerary must be a list"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    trip = cur.execute("SELECT id FROM trips WHERE id = ?", (trip_id,)).fetchone()
    if not trip:
        conn.close()
        return jsonify({"error": "Trip not found"}), 404

    cur.execute(
        """
        INSERT INTO itinerary (trip_id, data, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(trip_id) DO UPDATE SET
            data = excluded.data,
            updated_at = excluded.updated_at
        """,
        (trip_id, json.dumps(itinerary), datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()

    return jsonify({"success": True, "itinerary": itinerary})


@app.route("/api/trips/<trip_id>", methods=["PUT"])
def update_trip(trip_id):
    payload = request.get_json(silent=True) or {}
    name = payload.get("name")
    destination = payload.get("destination")

    if name is not None:
        name = name.strip()
        if not name:
            return jsonify({"error": "Trip name cannot be empty"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    exists = cur.execute("SELECT id FROM trips WHERE id = ?", (trip_id,)).fetchone()
    if not exists:
        conn.close()
        return jsonify({"error": "Trip not found"}), 404

    if name is not None:
        cur.execute("UPDATE trips SET name = ? WHERE id = ?", (name, trip_id))
    if destination is not None:
        cur.execute("UPDATE trips SET destination = ? WHERE id = ?", (destination.strip(), trip_id))

    conn.commit()
    trip = cur.execute(
        "SELECT id, name, destination, created, is_current FROM trips WHERE id = ?",
        (trip_id,),
    ).fetchone()
    conn.close()

    return jsonify({"trip": dict(trip)})


@app.route("/api/trips/<trip_id>", methods=["DELETE"])
def delete_trip(trip_id):
    conn = get_db_connection()
    cur = conn.cursor()

    trip = cur.execute("SELECT id, is_current FROM trips WHERE id = ?", (trip_id,)).fetchone()
    if not trip:
        conn.close()
        return jsonify({"error": "Trip not found"}), 404

    cur.execute("DELETE FROM trips WHERE id = ?", (trip_id,))

    if trip["is_current"] == 1:
        next_trip = cur.execute(
            "SELECT id FROM trips ORDER BY created DESC, id DESC LIMIT 1"
        ).fetchone()
        if next_trip:
            cur.execute("UPDATE trips SET is_current = 0")
            cur.execute("UPDATE trips SET is_current = 1 WHERE id = ?", (next_trip["id"],))

    conn.commit()
    conn.close()

    return jsonify({"success": True})


@app.route("/api/trips/<trip_id>/set-current", methods=["PUT"])
def set_current_trip(trip_id):
    conn = get_db_connection()
    cur = conn.cursor()

    trip = cur.execute("SELECT id FROM trips WHERE id = ?", (trip_id,)).fetchone()
    if not trip:
        conn.close()
        return jsonify({"error": "Trip not found"}), 404

    cur.execute("UPDATE trips SET is_current = 0")
    cur.execute("UPDATE trips SET is_current = 1 WHERE id = ?", (trip_id,))
    conn.commit()

    current = cur.execute(
        "SELECT id, name, destination, created, is_current FROM trips WHERE id = ?",
        (trip_id,),
    ).fetchone()
    conn.close()

    return jsonify({"trip": dict(current)})


@app.route("/api/trips/<trip_id>/members", methods=["POST"])
def add_member(trip_id):
    payload = request.get_json(silent=True) or {}
    name = normalize_name(payload.get("name"))

    if not name:
        return jsonify({"error": "Member name is required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    trip = cur.execute("SELECT id FROM trips WHERE id = ?", (trip_id,)).fetchone()
    if not trip:
        conn.close()
        return jsonify({"error": "Trip not found"}), 404

    existing = cur.execute(
        "SELECT id FROM members WHERE trip_id = ? AND name = ?", (trip_id, name)
    ).fetchone()
    if existing:
        conn.close()
        return jsonify({"error": "Member already exists"}), 400

    member_id = make_id()
    cur.execute(
        "INSERT INTO members (id, trip_id, name) VALUES (?, ?, ?)",
        (member_id, trip_id, name),
    )
    conn.commit()

    member = cur.execute(
        "SELECT id, trip_id, name FROM members WHERE id = ?", (member_id,)
    ).fetchone()
    conn.close()

    return jsonify({"member": dict(member)}), 201


@app.route("/api/trips/<trip_id>/members/<member_name>", methods=["DELETE"])
def remove_member(trip_id, member_name):
    member_name = normalize_name(member_name)

    conn = get_db_connection()
    cur = conn.cursor()

    member = cur.execute(
        "SELECT id FROM members WHERE trip_id = ? AND name = ?",
        (trip_id, member_name),
    ).fetchone()
    if not member:
        conn.close()
        return jsonify({"error": "Member not found"}), 404

    involved = cur.execute(
        """
        SELECT id, participants, receiver
        FROM transactions
        WHERE trip_id = ? AND (payer = ? OR receiver = ?)
        LIMIT 1
        """,
        (trip_id, member_name, member_name),
    ).fetchone()

    if not involved:
        tx_rows = cur.execute(
            "SELECT id, participants FROM transactions WHERE trip_id = ?",
            (trip_id,),
        ).fetchall()
        for tx_row in tx_rows:
            tx_participants = parse_beneficiaries(tx_row["participants"])
            if member_name in tx_participants:
                involved = tx_row
                break

    if involved:
        conn.close()
        return jsonify({"error": "Cannot remove member used in transactions"}), 400

    cur.execute(
        "DELETE FROM members WHERE trip_id = ? AND name = ?",
        (trip_id, member_name),
    )
    conn.commit()
    conn.close()

    return jsonify({"success": True})


@app.route("/api/trips/<trip_id>/transactions", methods=["POST"])
def add_transaction(trip_id):
    payload = request.get_json(silent=True) or {}

    tx_type = (payload.get("type") or "").strip().lower()
    desc = (payload.get("desc") or "").strip()
    reference = (payload.get("reference") or "").strip()
    category = (payload.get("category") or "other").strip().lower()
    amount = payload.get("amount")
    payer = normalize_name(payload.get("payer"))
    receiver = normalize_name(payload.get("receiver"))
    participants = parse_beneficiaries(payload.get("participants"))
    tx_date = (payload.get("date") or "").strip()
    if not tx_date:
        tx_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if tx_type not in {"expense", "transfer"}:
        return jsonify({"error": "Transaction type is required"}), 400

    if tx_type == "expense" and not desc:
        return jsonify({"error": "Description is required"}), 400

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return jsonify({"error": "Amount must be a number"}), 400

    if amount <= 0:
        return jsonify({"error": "Amount must be greater than 0"}), 400

    if not payer:
        return jsonify({"error": "Payer is required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    trip = cur.execute("SELECT id FROM trips WHERE id = ?", (trip_id,)).fetchone()
    if not trip:
        conn.close()
        return jsonify({"error": "Trip not found"}), 404

    member_rows = cur.execute(
        "SELECT name FROM members WHERE trip_id = ?", (trip_id,)
    ).fetchall()
    member_names = {row["name"] for row in member_rows}

    if payer not in member_names:
        conn.close()
        return jsonify({"error": "Payer must be a trip member"}), 400

    if tx_type == "transfer":
        if not receiver:
            conn.close()
            return jsonify({"error": "Receiver is required"}), 400
        if receiver not in member_names:
            conn.close()
            return jsonify({"error": "Receiver must be a trip member"}), 400
        # For transfers, desc should be "Transfer from X to Y"
        desc = f"Transfer from {payer} to {receiver}"
        participants = []
        category = None
    else:
        if not participants:
            conn.close()
            return jsonify({"error": "At least one participant is required"}), 400
        for name in participants:
            if name not in member_names:
                conn.close()
                return jsonify({"error": f"Participant {name} is not a trip member"}), 400
        # For expenses, reference defaults to desc if not provided
        if not reference:
            reference = desc

    tx_id = make_id()
    cur.execute(
        """
        INSERT INTO transactions
        (id, trip_id, type, desc, category, amount, payer, receiver, participants, date, reference)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            tx_id,
            trip_id,
            tx_type,
            desc,
            category,
            amount,
            payer,
            receiver,
            json.dumps(participants),
            tx_date,
            reference,
        ),
    )
    conn.commit()

    tx = cur.execute(
        """
        SELECT id, trip_id, type, desc, category, amount, payer, receiver, participants, date, reference
        FROM transactions
        WHERE id = ?
        """,
        (tx_id,),
    ).fetchone()
    conn.close()

    return jsonify({"transaction": dict(tx)}), 201


@app.route("/api/trips/<trip_id>/transactions/<tx_id>", methods=["DELETE"])
def delete_transaction(trip_id, tx_id):
    conn = get_db_connection()
    cur = conn.cursor()

    tx = cur.execute(
        "SELECT id FROM transactions WHERE id = ? AND trip_id = ?", (tx_id, trip_id)
    ).fetchone()
    if not tx:
        conn.close()
        return jsonify({"error": "Transaction not found"}), 404

    cur.execute("DELETE FROM transactions WHERE id = ? AND trip_id = ?", (tx_id, trip_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True})


@app.route("/api/trips/<trip_id>/transactions/<tx_id>", methods=["PUT"])
def update_transaction(trip_id, tx_id):
    payload = request.get_json(silent=True) or {}
    tx_type = (payload.get("type") or "").strip().lower()
    desc = (payload.get("desc") or "").strip()
    category = (payload.get("category") or "other").strip().lower()
    amount = payload.get("amount")
    payer = normalize_name(payload.get("payer"))
    receiver = normalize_name(payload.get("receiver"))
    participants = parse_beneficiaries(payload.get("participants"))
    tx_date = (payload.get("date") or "").strip()
    if not tx_date:
        tx_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if tx_type not in {"expense", "transfer"}:
        return jsonify({"error": "Transaction type is required"}), 400

    if tx_type == "expense" and not desc:
        return jsonify({"error": "Description is required"}), 400

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return jsonify({"error": "Amount must be a number"}), 400

    if amount <= 0:
        return jsonify({"error": "Amount must be greater than 0"}), 400

    if not payer:
        return jsonify({"error": "Payer is required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    tx = cur.execute(
        "SELECT id FROM transactions WHERE id = ? AND trip_id = ?",
        (tx_id, trip_id),
    ).fetchone()
    if not tx:
        conn.close()
        return jsonify({"error": "Transaction not found"}), 404

    member_rows = cur.execute(
        "SELECT name FROM members WHERE trip_id = ?",
        (trip_id,),
    ).fetchall()
    member_names = {row["name"] for row in member_rows}

    if payer not in member_names:
        conn.close()
        return jsonify({"error": "Payer must be a trip member"}), 400

    if tx_type == "transfer":
        if not receiver:
            conn.close()
            return jsonify({"error": "Receiver is required"}), 400
        if receiver not in member_names:
            conn.close()
            return jsonify({"error": "Receiver must be a trip member"}), 400
        participants = []
        category = None
    else:
        if not participants:
            conn.close()
            return jsonify({"error": "At least one participant is required"}), 400
        for name in participants:
            if name not in member_names:
                conn.close()
                return jsonify({"error": f"Participant {name} is not a trip member"}), 400

    cur.execute(
        """
        UPDATE transactions
        SET type = ?, desc = ?, category = ?, amount = ?, payer = ?, receiver = ?, participants = ?, date = ?, reference = ?
        WHERE id = ? AND trip_id = ?
        """,
        (
            tx_type,
            desc,
            category,
            amount,
            payer,
            receiver,
            json.dumps(participants),
            tx_date,
            desc,
            tx_id,
            trip_id,
        ),
    )
    conn.commit()

    updated = cur.execute(
        """
        SELECT id, trip_id, type, desc, category, amount, payer, receiver, participants, date, reference
        FROM transactions
        WHERE id = ? AND trip_id = ?
        """,
        (tx_id, trip_id),
    ).fetchone()
    conn.close()

    return jsonify({"transaction": dict(updated)})


@app.route("/api/trips/<trip_id>/settle", methods=["GET"])
def settle_trip(trip_id):
    conn = get_db_connection()
    cur = conn.cursor()

    trip = cur.execute("SELECT id FROM trips WHERE id = ?", (trip_id,)).fetchone()
    if not trip:
        conn.close()
        return jsonify({"error": "Trip not found"}), 404

    members = [
        row["name"]
        for row in cur.execute(
            "SELECT name FROM members WHERE trip_id = ? ORDER BY name ASC", (trip_id,)
        ).fetchall()
    ]

    txs = cur.execute(
        """
        SELECT id, type, desc, category, amount, payer, receiver, participants, date, reference
        FROM transactions
        WHERE trip_id = ?
        ORDER BY date DESC, id DESC
        """,
        (trip_id,),
    ).fetchall()
    conn.close()

    balances = {m: 0.0 for m in members}
    transaction_summaries = []

    for tx in txs:
        amount = float(tx["amount"])
        payer = normalize_name(tx["payer"])
        tx_type = (tx["type"] or "expense").lower()
        receiver = normalize_name(tx["receiver"])
        participants = parse_beneficiaries(tx["participants"])

        if tx_type == "transfer":
            if payer in balances:
                balances[payer] += amount
            if receiver in balances:
                balances[receiver] -= amount

            transaction_summaries.append(
                {
                    "id": tx["id"],
                    "type": "transfer",
                    "desc": tx["desc"],
                    "amount": round(amount, 2),
                    "payer": payer,
                    "receiver": receiver,
                    "net_effect": {
                        "payer": round(amount, 2),
                        "receiver": round(-amount, 2) if receiver else None,
                    },
                }
            )
            continue

        if payer in balances:
            balances[payer] += amount

        if participants:
            split = amount / len(participants)
            for person in participants:
                if person in balances:
                    balances[person] -= split

        transaction_summaries.append(
            {
                "id": tx["id"],
                "type": "expense",
                "desc": tx["desc"],
                "category": tx["category"],
                "amount": round(amount, 2),
                "payer": payer,
                "participants": participants,
                "share": round(amount / len(participants), 2) if participants else round(amount, 2),
            }
        )

    rounded_balances = {k: round(v, 2) for k, v in balances.items()}

    creditors = []
    debtors = []
    for name, bal in rounded_balances.items():
        if bal > 0.01:
            creditors.append([name, bal])
        elif bal < -0.01:
            debtors.append([name, -bal])

    creditors.sort(key=lambda x: x[1], reverse=True)
    debtors.sort(key=lambda x: x[1], reverse=True)

    settlements = []
    while creditors and debtors:
        debtor_name, debt = debtors[0]
        creditor_name, credit = creditors[0]

        transfer = round(min(debt, credit), 2)
        settlements.append({"from": debtor_name, "to": creditor_name, "amount": transfer})

        debt = round(debt - transfer, 2)
        credit = round(credit - transfer, 2)

        if debt <= 0.01:
            debtors.pop(0)
        else:
            debtors[0][1] = debt

        if credit <= 0.01:
            creditors.pop(0)
        else:
            creditors[0][1] = credit

        creditors.sort(key=lambda x: x[1], reverse=True)
        debtors.sort(key=lambda x: x[1], reverse=True)

    return jsonify({"balances": rounded_balances, "settlements": settlements, "transaction_summaries": transaction_summaries})


@app.route("/")
def serve_index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory(STATIC_DIR, filename)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8000, debug=False)
