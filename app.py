from flask import Flask, request, redirect, session, render_template_string, url_for
import sqlite3
import random
import os

app = Flask(__name__)
app.secret_key = "super_secret_key"

DB_PATH = "/app/casino.db"   # Fly.io 볼륨 경로


# -----------------------
# DB 초기화
# -----------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            balance INTEGER DEFAULT 1000,
            is_admin INTEGER DEFAULT 0
        )
    """)

    # 관리자 자동 생성
    cur.execute("SELECT * FROM users WHERE username='admin'")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO users (username, password, balance, is_admin)
            VALUES (?, ?, ?, ?)
        """, ("admin", "admin1234", 1000000, 1))
        conn.commit()

    conn.commit()
    conn.close()


def get_user(username):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, username, password, balance, is_admin FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()
    return row


def update_balance(username, new_balance):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance=? WHERE username=?", (new_balance, username))
    conn.commit()
    conn.close()


# -----------------------
# HTML 템플릿 (강력 버전)
# -----------------------
TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>🎰 Casino Server</title>
<style>
body { margin:0; background:#0a0a15; font-family:system-ui; color:white; }
.center { width:420px; margin:40px auto; background:rgba(255,255,255,0.07); padding:20px; border-radius:12px; }
input { width:100%; padding:10px; border-radius:8px; border:none; margin-bottom:10px; }
button { width:100%; padding:10px; margin-top:10px; border:none; border-radius:8px; font-size:15px; cursor:pointer; }
.btn1 { background:#ff6b6b; }
.btn2 { background:#333; color:white; }
a { color:#ffd86b; }

/* 슬롯머신 */
.card { width:420px; margin:40px auto; background:rgba(255,255,255,0.05); padding:20px; border-radius:12px; }
.reels { display:flex; justify-content:space-between; margin-bottom:10px; }
.reel { width:100px; height:80px; background:#111830; display:flex; justify-content:center; align-items:center;
        font-size:35px; border-radius:8px; }
.balance-box { display:flex; justify-content:space-between; background:#151a2d; padding:12px; border-radius:8px; margin-bottom:12px; }

</style>
</head>
<body>

{% if not username %}
<div class="center">
<h2>🔑 로그인</h2>
<form method="POST">
<input name="username" placeholder="아이디">
<input name="password" type="password" placeholder="비밀번호">
<button class="btn1">로그인</button>
</form>
<br>
<a href="{{ url_for('register') }}">회원가입 →</a>
</div>
{% endif %}

{% if page == "register" %}
<div class="center">
<h2>📝 회원가입</h2>
<form method="POST">
<input name="username" placeholder="아이디">
<input name="password" type="password" placeholder="비밀번호">
<button class="btn1">가입하기</button>
</form>
</div>
{% endif %}

{% if username and page == "lobby" %}
<div class="center">
<h2>🎮 게임 선택</h2>
<div class="balance-box">
<span>{{username}}</span>
<b>{{balance}}</b>
</div>

<button class="btn1" onclick="location.href='{{ url_for('slot') }}'">🎰 슬롯머신</button>
<button class="btn1" onclick="location.href='{{ url_for('roulette') }}'">🎯 룰렛</button>
<button class="btn1" onclick="location.href='{{ url_for('blackjack') }}'">🃏 블랙잭</button>

{% if is_admin %}
<br><br>
<button class="btn2" onclick="location.href='{{ url_for('admin') }}'">👑 관리자 페이지</button>
{% endif %}

<br><br>
<a href="{{ url_for('logout') }}">로그아웃</a>
</div>
{% endif %}

{% if username and page == "slot" %}
<div class="card">
<h2>🎰 슬롯머신</h2>

<div class="balance-box"><span>보유</span><b id="bal">{{balance}}</b></div>

<div class="reels">
<div class="reel" id="r1">🍒</div>
<div class="reel" id="r2">🍋</div>
<div class="reel" id="r3">⭐</div>
</div>

<input id="bet" type="number" value="50" min="10">
<button class="btn1" onclick="spin()">스핀</button>
<button class="btn2" onclick="location.href='{{ url_for('lobby') }}'">뒤로</button>

<p id="msg"></p>
</div>

<script>
function spin(){
let bet = document.getElementById("bet").value;
fetch("/slot_play", {method:"POST", headers:{'Content-Type': 'application/x-www-form-urlencoded'}, body:"bet="+bet})
.then(r=>r.json())
.then(d=>{
document.getElementById("r1").innerText=d.s1;
document.getElementById("r2").innerText=d.s2;
document.getElementById("r3").innerText=d.s3;
document.getElementById("bal").innerText=d.balance;
document.getElementById("msg").innerText=d.msg;
});
}
</script>
{% endif %}


</body>
</html>
"""


# -----------------------
# 라우트
# -----------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = get_user(username)
        if not user or user[2] != password:
            return render_template_string(TEMPLATE, page="login", username=None)

        session["username"] = user[1]
        session["balance"] = user[3]
        session["is_admin"] = bool(user[4])
        return redirect("/lobby")

    return render_template_string(TEMPLATE, page="login", username=None)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username, password) VALUES (?,?)", (username, password))
            conn.commit()
        except:
            pass
        conn.close()

        return redirect("/")

    return render_template_string(TEMPLATE, page="register", username=None)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/lobby")
def lobby():
    if "username" not in session:
        return redirect("/")
    return render_template_string(
        TEMPLATE,
        page="lobby",
        username=session["username"],
        balance=session["balance"],
        is_admin=session["is_admin"],
    )


@app.route("/slot")
def slot():
    if "username" not in session:
        return redirect("/")
    return render_template_string(
        TEMPLATE,
        page="slot",
        username=session["username"],
        balance=session["balance"],
        is_admin=session["is_admin"],
    )


# -----------------------
# API: 슬롯머신
# -----------------------
@app.route("/slot_play", methods=["POST"])
def slot_play():
    if "username" not in session:
        return {"error": "로그인 필요"}

    bet = int(request.form["bet"])

    user = get_user(session["username"])
    balance = user[3]

    if bet > balance:
        return {"error": "포인트 부족"}

    balance -= bet

    symbols = ["🍒","🍋","⭐","🍀","💎","7️⃣"]
    s1, s2, s3 = random.choice(symbols), random.choice(symbols), random.choice(symbols)

    msg = "❌ 꽝!"

    if s1 == s2 == s3:
        reward = bet * 10
        balance += reward
        msg = f"🎉 JACKPOT! +{reward}"
    elif s1 == s2 or s2 == s3 or s1 == s3:
        reward = bet * 2
        balance += reward
        msg = f"✨ 2개 일치 +{reward}"

    update_balance(user[1], balance)
    session["balance"] = balance

    return {"s1": s1, "s2": s2, "s3": s3, "balance": balance, "msg": msg}


# -----------------------
# 실행
# -----------------------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080)
