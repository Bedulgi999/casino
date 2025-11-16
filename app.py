from flask import Flask, request, redirect, session, render_template_string, url_for
import sqlite3
import random

app = Flask(__name__)
app.secret_key = "super_secret_key"
DB_PATH = "casino.db"


# ------------------------
# DB 초기화
# ------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            balance INTEGER DEFAULT 1000,
            is_admin INTEGER DEFAULT 0
        )
        """
    )

    # 관리자 계정 자동 생성
    cur.execute("SELECT * FROM users WHERE username='admin'")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (username, password, balance, is_admin) VALUES (?, ?, ?, ?)",
            ("admin", "admin1234", 1000000, 1),
        )
        print("✅ Admin created: admin / admin1234")

    conn.commit()
    conn.close()


def get_user(username):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, password, balance, is_admin FROM users WHERE username=?",
        (username,),
    )
    row = cur.fetchone()
    conn.close()
    return row


def update_balance(username, new_balance):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance=? WHERE username=?", (new_balance, username))
    conn.commit()
    conn.close()


# ------------------------
# HTML 템플릿 (한 파일 안에 모두)
# ------------------------
TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <title>🎰 포인트 카지노 데모</title>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: radial-gradient(circle at top, #242654, #05030a);
      color: #fff;
    }
    a { color: #ffd76a; text-decoration: none; }
    a:hover { text-decoration: underline; }

    .nav {
      display:flex;
      justify-content:space-between;
      align-items:center;
      padding:12px 22px;
      background:rgba(0,0,0,0.6);
      border-bottom:1px solid rgba(255,255,255,0.1);
      position:sticky;
      top:0;
      backdrop-filter: blur(10px);
      z-index:10;
    }
    .nav .logo { font-weight:700; font-size:18px; }
    .nav .nav-right { font-size:14px; display:flex; gap:12px; align-items:center; }
    .pill {
      padding:4px 10px;
      border-radius:999px;
      background:rgba(0,0,0,0.4);
      font-size:12px;
    }

    .page-wrap {
      min-height:100vh;
      display:flex;
      justify-content:center;
      align-items:flex-start;
      padding:40px 16px 60px;
    }
    .card, .auth-card {
      background: rgba(0, 0, 0, 0.55);
      border-radius: 20px;
      padding: 24px 26px 30px;
      width: 420px;
      box-shadow: 0 18px 35px rgba(0, 0, 0, 0.7);
      border: 1px solid rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(14px);
    }
    .auth-card h1, .card h1 { margin-top:0; text-align:center; }
    .input {
      width:100%;
      padding:10px 12px;
      border-radius:10px;
      border:1px solid rgba(255,255,255,0.25);
      outline:none;
      margin-bottom:12px;
      background:rgba(0,0,0,0.4);
      color:#fff;
    }
    .btn {
      width:100%;
      padding:10px 14px;
      border-radius:999px;
      border:none;
      cursor:pointer;
      font-weight:600;
      margin-top:6px;
      font-size:15px;
      transition: transform 0.08s ease, box-shadow 0.12s ease, opacity 0.12s ease;
    }
    .btn:active {
      transform:scale(0.97) translateY(1px);
      box-shadow:none;
    }
    .btn-primary {
      background:linear-gradient(135deg, #ffb347, #ff6b6b);
      color:#1b0b00;
      box-shadow:0 12px 24px rgba(255,107,107,0.55);
    }
    .btn-secondary {
      background:rgba(255,255,255,0.12);
      color:#fff;
      box-shadow:0 10px 20px rgba(0,0,0,0.6);
    }
    .subtitle {
      text-align:center;
      font-size:13px;
      color:#ccc;
      margin-bottom:18px;
    }
    .link-row {
      margin-top:10px;
      text-align:center;
      font-size:13px;
      color:#bbb;
    }

    .balance-box {
      display:flex;
      justify-content:space-between;
      align-items:center;
      padding:10px 14px;
      border-radius:13px;
      background:rgba(15, 15, 40, 0.9);
      margin-bottom:16px;
      font-size:14px;
    }
    .balance-box span.amount {
      font-weight:700;
      font-size:18px;
      color:#ffdd55;
    }
    .game-area {
      border-radius:16px;
      background:rgba(7, 7, 30, 0.95);
      padding:18px 16px 16px;
      border:1px solid rgba(255,255,255,0.05);
    }
    .reels {
      display:flex;
      justify-content:space-between;
      margin-bottom:12px;
    }
    .reel {
      flex: 1;
      margin: 0 4px;
      height: 70px;
      border-radius: 12px;
      background: linear-gradient(135deg, #10132f, #1b1f4b);
      display: flex;
      justify-content: center;
      align-items: center;
      font-size: 34px;
      border: 1px solid rgba(255, 255, 255, 0.08);
      box-shadow: 0 8px 15px rgba(0, 0, 0, 0.45);
    }
    .bet-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      font-size: 14px;
      gap:8px;
    }
    .bet-row input {
      width: 120px;
      padding: 6px 8px;
      border-radius: 8px;
      border: 1px solid rgba(255, 255, 255, 0.2);
      background: rgba(0, 0, 0, 0.4);
      color: #fff;
      outline: none;
      text-align: right;
    }
    .buttons {
      display: flex;
      gap: 10px;
      margin-bottom: 10px;
    }
    .msg {
      min-height: 20px;
      font-size: 13px;
      color: #ccc;
      text-align:center;
      margin-top:6px;
    }
    .msg.win { color:#ffd95e; }
    .msg.lose { color:#ff8181; }

    .game-grid {
      display:grid;
      grid-template-columns:repeat(3, minmax(0,1fr));
      gap:12px;
    }
    .game-tile {
      border-radius:16px;
      padding:14px 12px;
      background:rgba(0,0,0,0.5);
      cursor:pointer;
      border:1px solid transparent;
      transition:transform 0.08s ease, box-shadow 0.1s ease, border-color 0.1s ease;
    }
    .game-tile:hover {
      transform:translateY(-2px);
      box-shadow:0 10px 20px rgba(0,0,0,0.6);
      border-color:rgba(255,255,255,0.18);
    }
    .game-tile-title { font-size:15px; font-weight:600; margin-bottom:6px; }
    .game-tile-desc { font-size:12px; color:#ccc; }

    table {
      width:100%;
      border-collapse:collapse;
      font-size:13px;
    }
    th, td {
      padding:6px 8px;
      border-bottom:1px solid rgba(255,255,255,0.08);
      text-align:left;
    }
    th { font-size:12px; text-transform:uppercase; letter-spacing:0.03em; color:#aaa; }

    .admin-form {
      margin-top:14px;
      padding-top:10px;
      border-top:1px dashed rgba(255,255,255,0.2);
      font-size:13px;
    }
    .admin-form-row {
      display:flex;
      gap:8px;
      margin-bottom:6px;
    }
    .admin-form-row input, .admin-form-row select {
      flex:1;
      padding:6px 8px;
      border-radius:8px;
      border:1px solid rgba(255,255,255,0.2);
      background:rgba(0,0,0,0.4);
      color:#fff;
      font-size:13px;
    }

    .badge-admin {
      padding:2px 6px;
      border-radius:999px;
      background:rgba(255,215,106,0.1);
      border:1px solid rgba(255,215,106,0.4);
      color:#ffd76a;
      font-size:11px;
    }

    .roulette-layout {
      margin-top:10px;
      font-size:14px;
    }
    .roulette-row {
      display:flex;
      gap:8px;
      margin-bottom:10px;
    }
    .roulette-row select, .roulette-row input {
      flex:1;
      padding:8px 10px;
      border-radius:8px;
      border:1px solid rgba(255,255,255,0.2);
      background:rgba(0,0,0,0.4);
      color:#fff;
    }
    .roulette-wheel {
      margin:0 auto 10px;
      width:140px;
      height:140px;
      border-radius:50%;
      border:4px solid rgba(255,255,255,0.3);
      display:flex;
      align-items:center;
      justify-content:center;
      font-size:26px;
      background:conic-gradient(#e74c3c 0 120deg, #2ecc71 120deg 180deg, #2c3e50 180deg 360deg);
      position:relative;
      overflow:hidden;
    }
    .pointer {
      position:absolute;
      top:-6px;
      left:50%;
      transform:translateX(-50%);
      width:0;
      height:0;
      border-left:8px solid transparent;
      border-right:8px solid transparent;
      border-bottom:12px solid #fff;
    }
    .wheel-number {
      background:rgba(0,0,0,0.65);
      padding:6px 12px;
      border-radius:999px;
      border:1px solid rgba(255,255,255,0.5);
    }

    .bj-row {
      display:flex;
      justify-content:space-between;
      margin-bottom:6px;
      font-size:14px;
    }
    .bj-hand {
      padding:8px 10px;
      border-radius:10px;
      background:rgba(0,0,0,0.4);
      margin-bottom:10px;
      font-size:16px;
    }
  </style>
</head>
<body>
  {% if username %}
  <div class="nav">
    <div class="logo">🎰 Dove Casino Demo</div>
    <div class="nav-right">
      <span class="pill">{{ username }} · {{ balance }} P</span>
      {% if is_admin %}
      <a href="{{ url_for('admin') }}">관리자</a>
      {% endif %}
      <a href="{{ url_for('logout') }}">로그아웃</a>
    </div>
  </div>
  {% endif %}

  <div class="page-wrap">
    {% if page == 'login' %}
      <div class="auth-card">
        <h1>로그인</h1>
        <p class="subtitle">가상 포인트로 즐기는 연습용 카지노입니다.</p>
        <form method="POST">
          <input class="input" name="username" placeholder="아이디" required>
          <input class="input" name="password" type="password" placeholder="비밀번호" required>
          <button class="btn btn-primary" type="submit">로그인</button>
        </form>
        <div class="link-row">
          계정이 없나요?
          <a href="{{ url_for('register') }}">회원가입</a>
        </div>
      </div>

    {% elif page == 'register' %}
      <div class="auth-card">
        <h1>회원가입</h1>
        <p class="subtitle">가입 시 기본 포인트 1000P가 지급됩니다.</p>
        <form method="POST">
          <input class="input" name="username" placeholder="아이디" required>
          <input class="input" name="password" type="password" placeholder="비밀번호" required>
          <button class="btn btn-primary" type="submit">가입하기</button>
        </form>
        <div class="link-row">
          이미 계정이 있나요?
          <a href="{{ url_for('login') }}">로그인</a>
        </div>
      </div>

    {% elif page == 'lobby' %}
      <div class="card">
        <h1>게임 선택</h1>
        <p class="subtitle">원하는 게임을 선택해 연습해보세요.</p>
        <div class="balance-box">
          <span>보유 포인트</span>
          <span class="amount">{{ balance }}</span>
        </div>
        <div class="game-grid">
          <div class="game-tile" onclick="location.href='{{ url_for('slot') }}'">
            <div class="game-tile-title">🎰 슬롯머신</div>
            <div class="game-tile-desc">3개 일치 시 10배, 2개 일치 시 2배 지급</div>
          </div>
          <div class="game-tile" onclick="location.href='{{ url_for('roulette') }}'">
            <div class="game-tile-title">🎯 룰렛</div>
            <div class="game-tile-desc">빨강/검정/그린에 베팅해보세요</div>
          </div>
          <div class="game-tile" onclick="location.href='{{ url_for('blackjack') }}'">
            <div class="game-tile-title">🃏 블랙잭(라운드)</div>
            <div class="game-tile-desc">간단 버전: 한 번에 승/패/무 판정</div>
          </div>
        </div>
      </div>

    {% elif page == 'slot' %}
      <div class="card">
        <h1>🎰 슬롯머신</h1>
        <p class="subtitle">3개 일치 시 10배, 2개 일치 시 2배 (가상 포인트)</p>

        <div class="balance-box">
          <span>보유 포인트</span>
          <span class="amount" id="slot-balance">{{ balance }}</span>
        </div>

        <div class="game-area">
          <div class="reels">
            <div class="reel" id="r1">🍒</div>
            <div class="reel" id="r2">🍋</div>
            <div class="reel" id="r3">⭐</div>
          </div>

          <div class="bet-row">
            <span>베팅 포인트</span>
            <input type="number" id="slot-bet" min="10" step="10" value="50" />
          </div>

          <div class="buttons">
            <button class="btn btn-primary" id="slot-spin">스핀하기</button>
            <button class="btn btn-secondary" onclick="location.href='{{ url_for('lobby') }}'">게임 선택으로</button>
          </div>

          <div class="msg" id="slot-msg">스핀 버튼을 눌러 시작하세요.</div>
        </div>
      </div>

    {% elif page == 'roulette' %}
      <div class="card">
        <h1>🎯 룰렛</h1>
        <p class="subtitle">빨강/검정은 2배, 그린(0)은 14배 (가상 포인트)</p>

        <div class="balance-box">
          <span>보유 포인트</span>
          <span class="amount" id="roulette-balance">{{ balance }}</span>
        </div>

        <div class="game-area">
          <div class="roulette-wheel" id="roulette-wheel">
            <div class="pointer"></div>
            <div class="wheel-number" id="roulette-number">?</div>
          </div>

          <div class="roulette-layout">
            <div class="roulette-row">
              <select id="roulette-color">
                <option value="red">🔴 빨강</option>
                <option value="black">⚫ 검정</option>
                <option value="green">🟢 그린(0)</option>
              </select>
              <input id="roulette-bet" type="number" min="10" step="10" value="50" placeholder="베팅">
            </div>
            <button class="btn btn-primary" id="roulette-spin">스핀</button>
            <button class="btn btn-secondary" onclick="location.href='{{ url_for('lobby') }}'">게임 선택으로</button>
            <div class="msg" id="roulette-msg">색을 선택하고 베팅 후 스핀!</div>
          </div>
        </div>
      </div>

    {% elif page == 'blackjack' %}
      <div class="card">
        <h1>🃏 블랙잭 (단일 라운드)</h1>
        <p class="subtitle">간단 버전: 한 번에 승/패/무 결정 (21에 가까운 쪽 승리)</p>

        <div class="balance-box">
          <span>보유 포인트</span>
          <span class="amount" id="bj-balance">{{ balance }}</span>
        </div>

        <div class="game-area">
          <div class="bj-row">
            <span>플레이어</span>
            <span id="bj-player-score">-</span>
          </div>
          <div class="bj-hand" id="bj-player-hand">카드를 뽑아보세요.</div>
          <div class="bj-row">
            <span>딜러</span>
            <span id="bj-dealer-score">-</span>
          </div>
          <div class="bj-hand" id="bj-dealer-hand">-</div>

          <div class="bet-row">
            <span>베팅 포인트</span>
            <input type="number" id="bj-bet" min="10" step="10" value="50" />
          </div>

          <div class="buttons">
            <button class="btn btn-primary" id="bj-play">한 라운드 플레이</button>
            <button class="btn btn-secondary" onclick="location.href='{{ url_for('lobby') }}'">게임 선택으로</button>
          </div>

          <div class="msg" id="bj-msg">베팅 후 라운드를 시작하세요.</div>
        </div>
      </div>

    {% elif page == 'admin' %}
      <div class="card">
        <h1>👑 관리자 페이지</h1>
        <p class="subtitle">유저 포인트 조회 및 충전/차감</p>
        <div class="game-area">
          <table>
            <thead>
              <tr>
                <th>아이디</th>
                <th>포인트</th>
                <th>권한</th>
              </tr>
            </thead>
            <tbody>
              {% for u in users %}
              <tr>
                <td>{{ u[1] }}</td>
                <td>{{ u[3] }}</td>
                <td>
                  {% if u[4] %}
                    <span class="badge-admin">ADMIN</span>
                  {% else %}
                    -
                  {% endif %}
                </td>
              </tr>
              {% endfor %}
            </tbody>
          </table>

          <form class="admin-form" method="POST">
            <div>포인트 수정</div>
            <div class="admin-form-row">
              <input name="username" placeholder="아이디" required>
              <input name="amount" type="number" placeholder="포인트" required>
            </div>
            <div class="admin-form-row">
              <select name="action">
                <option value="add">충전 (+)</option>
                <option value="sub">차감 (-)</option>
                <option value="set">직접 설정 (=)</option>
              </select>
              <button class="btn btn-primary" type="submit">적용</button>
            </div>
          </form>

          <div class="link-row">
            <a href="{{ url_for('lobby') }}">게임 선택으로</a>
          </div>
        </div>
      </div>
    {% endif %}
  </div>

<script>
  const SLOT_SYMBOLS = ["🍒", "🍋", "⭐", "🍀", "💎", "7️⃣"];

  // ------- 슬롯머신 (스핀 모션) -------
  const slotSpinBtn = document.getElementById("slot-spin");
  if (slotSpinBtn) {
    const r1 = document.getElementById("r1");
    const r2 = document.getElementById("r2");
    const r3 = document.getElementById("r3");
    const slotBetInput = document.getElementById("slot-bet");
    const slotMsg = document.getElementById("slot-msg");
    const slotBal = document.getElementById("slot-balance");

    let spinning = false;
    let spinTimer = null;

    function randomSymbol() {
      const idx = Math.floor(Math.random() * SLOT_SYMBOLS.length);
      return SLOT_SYMBOLS[idx];
    }

    function startAnimation() {
      spinTimer = setInterval(() => {
        r1.textContent = randomSymbol();
        r2.textContent = randomSymbol();
        r3.textContent = randomSymbol();
      }, 80);
    }

    slotSpinBtn.addEventListener("click", () => {
      if (spinning) return;
      const bet = parseInt(slotBetInput.value || "0", 10);
      if (bet <= 0) {
        slotMsg.textContent = "베팅 포인트를 입력하세요. (최소 10)";
        return;
      }

      spinning = true;
      slotSpinBtn.disabled = true;
      slotMsg.textContent = "스핀 중...";
      startAnimation();

      fetch("{{ url_for('slot_play') }}", {
        method: "POST",
        headers: {"Content-Type": "application/x-www-form-urlencoded"},
        body: "bet=" + encodeURIComponent(bet)
      })
      .then(res => res.json())
      .then(data => {
        if (data.error) {
          clearInterval(spinTimer);
          spinTimer = null;
          slotMsg.textContent = data.error;
          spinning = false;
          slotSpinBtn.disabled = false;
          return;
        }
        setTimeout(() => {
          clearInterval(spinTimer);
          spinTimer = null;
          r1.textContent = data.s1;
          r2.textContent = data.s2;
          r3.textContent = data.s3;
          slotBal.textContent = data.balance;
          slotMsg.textContent = data.msg;
          spinning = false;
          slotSpinBtn.disabled = false;
        }, 900);
      })
      .catch(() => {
        clearInterval(spinTimer);
        spinTimer = null;
        slotMsg.textContent = "오류 발생";
        spinning = false;
        slotSpinBtn.disabled = false;
      });
    });
  }

  // ------- 룰렛 -------
  const rouletteSpinBtn = document.getElementById("roulette-spin");
  if (rouletteSpinBtn) {
    const wheel = document.getElementById("roulette-wheel");
    const numberEl = document.getElementById("roulette-number");
    const balEl = document.getElementById("roulette-balance");
    const colorSel = document.getElementById("roulette-color");
    const betInput = document.getElementById("roulette-bet");
    const msgEl = document.getElementById("roulette-msg");

    let spinning = false;

    rouletteSpinBtn.addEventListener("click", () => {
      if (spinning) return;
      const bet = parseInt(betInput.value || "0", 10);
      if (bet <= 0) {
        msgEl.textContent = "베팅 포인트를 입력하세요. (최소 10)";
        return;
      }
      const color = colorSel.value;
      spinning = true;
      rouletteSpinBtn.disabled = true;
      msgEl.textContent = "휠이 돌고 있습니다...";

      let angle = 0;
      const spinInterval = setInterval(() => {
        angle += 20;
        wheel.style.transform = "rotate(" + angle + "deg)";
      }, 40);

      fetch("{{ url_for('roulette_play') }}", {
        method: "POST",
        headers: {"Content-Type":"application/x-www-form-urlencoded"},
        body: "bet=" + encodeURIComponent(bet) + "&color=" + encodeURIComponent(color)
      })
      .then(res => res.json())
      .then(data => {
        setTimeout(() => {
          clearInterval(spinInterval);
          wheel.style.transform = "rotate(0deg)";
          numberEl.textContent = data.number + " " + (data.color_emoji || "");
          balEl.textContent = data.balance;
          msgEl.textContent = data.msg || "";
          spinning = false;
          rouletteSpinBtn.disabled = false;
        }, 900);
      })
      .catch(() => {
        clearInterval(spinInterval);
        msgEl.textContent = "오류 발생";
        spinning = false;
        rouletteSpinBtn.disabled = false;
      });
    });
  }

  // ------- 블랙잭 (단일 라운드) -------
  const bjBtn = document.getElementById("bj-play");
  if (bjBtn) {
    const balEl = document.getElementById("bj-balance");
    const betInput = document.getElementById("bj-bet");
    const playerScoreEl = document.getElementById("bj-player-score");
    const dealerScoreEl = document.getElementById("bj-dealer-score");
    const playerHandEl = document.getElementById("bj-player-hand");
    const dealerHandEl = document.getElementById("bj-dealer-hand");
    const msgEl = document.getElementById("bj-msg");

    bjBtn.addEventListener("click", () => {
      const bet = parseInt(betInput.value || "0", 10);
      if (bet <= 0) {
        msgEl.textContent = "베팅 포인트를 입력하세요. (최소 10)";
        return;
      }
      msgEl.textContent = "카드를 뽑는 중...";

      fetch("{{ url_for('blackjack_round') }}", {
        method: "POST",
        headers: {"Content-Type":"application/x-www-form-urlencoded"},
        body: "bet=" + encodeURIComponent(bet)
      })
      .then(res => res.json())
      .then(data => {
        balEl.textContent = data.balance;
        playerScoreEl.textContent = data.player_score;
        dealerScoreEl.textContent = data.dealer_score;
        playerHandEl.textContent = data.player_hand;
        dealerHandEl.textContent = data.dealer_hand;
        msgEl.textContent = data.msg;
      })
      .catch(() => {
        msgEl.textContent = "오류 발생";
      });
    });
  }
</script>

</body>
</html>
"""


# ------------------------
# 라우트
# ------------------------
@app.route("/")
def root():
    if "username" in session:
        return redirect(url_for("lobby"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        user = get_user(username)
        if not user or user[2] != password:
            return render_template_string(
                TEMPLATE,
                page="login",
                username=None,
                balance=0,
                is_admin=False,
            )
        session["username"] = user[1]
        session["balance"] = user[3]
        session["is_admin"] = bool(user[4])
        return redirect(url_for("lobby"))

    return render_template_string(
        TEMPLATE, page="login", username=None, balance=0, is_admin=False
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        if not username or not password:
            return render_template_string(
                TEMPLATE, page="register", username=None, balance=0, is_admin=False
            )
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (username, password, balance, is_admin) VALUES (?, ?, ?, 0)",
                (username, password, 1000),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "이미 존재하는 아이디입니다."
        conn.close()
        return redirect(url_for("login"))

    return render_template_string(
        TEMPLATE, page="register", username=None, balance=0, is_admin=False
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


def require_login():
    return "username" in session


@app.route("/lobby")
def lobby():
    if not require_login():
        return redirect(url_for("login"))
    return render_template_string(
        TEMPLATE,
        page="lobby",
        username=session["username"],
        balance=session["balance"],
        is_admin=session["is_admin"],
    )


@app.route("/slot")
def slot():
    if not require_login():
        return redirect(url_for("login"))
    return render_template_string(
        TEMPLATE,
        page="slot",
        username=session["username"],
        balance=session["balance"],
        is_admin=session["is_admin"],
    )


@app.route("/roulette")
def roulette():
    if not require_login():
        return redirect(url_for("login"))
    return render_template_string(
        TEMPLATE,
        page="roulette",
        username=session["username"],
        balance=session["balance"],
        is_admin=session["is_admin"],
    )


@app.route("/blackjack")
def blackjack():
    if not require_login():
        return redirect(url_for("login"))
    return render_template_string(
        TEMPLATE,
        page="blackjack",
        username=session["username"],
        balance=session["balance"],
        is_admin=session["is_admin"],
    )


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not require_login() or not session.get("is_admin"):
        return "관리자만 접근 가능합니다."

    if request.method == "POST":
        username = request.form["username"].strip()
        try:
            amount = int(request.form["amount"])
        except ValueError:
            amount = 0
        action = request.form["action"]

        user = get_user(username)
        if user:
            current = user[3]
            if action == "add":
                new_bal = current + amount
            elif action == "sub":
                new_bal = max(0, current - amount)
            else:  # set
                new_bal = amount

            update_balance(username, new_bal)

            # 본인 계정 수정이면 세션도 갱신
            if username == session["username"]:
                session["balance"] = new_bal

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, username, password, balance, is_admin FROM users")
    users = conn.cursor().fetchall() if False else cur.fetchall()
    conn.close()

    return render_template_string(
        TEMPLATE,
        page="admin",
        username=session["username"],
        balance=session["balance"],
        is_admin=session["is_admin"],
        users=users,
    )


# ------------------------
# 게임 API
# ------------------------
@app.route("/slot_play", methods=["POST"])
def slot_play():
    if not require_login():
        return {"error": "로그인이 필요합니다."}

    try:
        bet = int(request.form["bet"])
    except (KeyError, ValueError):
        return {"error": "잘못된 베팅 금액"}

    user = get_user(session["username"])
    balance = user[3]

    if bet <= 0 or bet > balance:
        return {"error": "포인트가 부족하거나 금액이 잘못되었습니다."}

    symbols = ["🍒", "🍋", "⭐", "🍀", "💎", "7️⃣"]
    s1 = random.choice(symbols)
    s2 = random.choice(symbols)
    s3 = random.choice(symbols)

    balance -= bet
    msg = "❌ 꽝!"

    if s1 == s2 == s3:
        reward = bet * 10
        balance += reward
        msg = f"🎉 JACKPOT! +{reward}"
    elif s1 == s2 or s2 == s3 or s1 == s3:
        reward = bet * 2
        balance += reward
        msg = f"✨ 2개 일치! +{reward}"

    update_balance(user[1], balance)
    session["balance"] = balance

    return {"s1": s1, "s2": s2, "s3": s3, "balance": balance, "msg": msg}


@app.route("/roulette_play", methods=["POST"])
def roulette_play():
    if not require_login():
        return {"error": "로그인이 필요합니다."}

    try:
        bet = int(request.form["bet"])
    except (KeyError, ValueError):
        return {"error": "잘못된 베팅 금액"}

    color = request.form.get("color", "red")

    user = get_user(session["username"])
    balance = user[3]

    if bet <= 0 or bet > balance:
        return {"error": "포인트가 부족하거나 금액이 잘못되었습니다."}

    # 0~36
    number = random.randint(0, 36)
    if number == 0:
        winning_color = "green"
        emoji = "🟢"
    elif number % 2 == 0:
        winning_color = "black"
        emoji = "⚫"
    else:
        winning_color = "red"
        emoji = "🔴"

    balance -= bet
    msg = "❌ 패배!"

    if winning_color == color:
        if winning_color == "green":
            reward = bet * 14
        else:
            reward = bet * 2
        balance += reward
        msg = f"🎉 승리! +{reward}"

    update_balance(user[1], balance)
    session["balance"] = balance

    return {
        "number": number,
        "color": winning_color,
        "color_emoji": emoji,
        "balance": balance,
        "msg": msg,
    }


@app.route("/blackjack_round", methods=["POST"])
def blackjack_round():
    if not require_login():
        return {"error": "로그인이 필요합니다."}

    try:
        bet = int(request.form["bet"])
    except (KeyError, ValueError):
        return {"error": "잘못된 베팅 금액"}

    user = get_user(session["username"])
    balance = user[3]

    if bet <= 0 or bet > balance:
        return {"error": "포인트가 부족하거나 금액이 잘못되었습니다."}

    balance -= bet

    # 간단 버전: 카드 값 랜덤으로 몇 장 뽑아서 점수 생성
    def draw_hand():
        cards = []
        total = 0
        while total < random.randint(12, 20):
            v = random.randint(2, 11)
            cards.append(v)
            total += v
        return cards, total

    player_cards, player_score = draw_hand()
    dealer_cards, dealer_score = draw_hand()

    if player_score > 21:
        msg = "💥 플레이어 버스트! 패배"
    elif dealer_score > 21 or player_score > dealer_score:
        win = bet * 2
        balance += win
        msg = f"🎉 승리! +{win}"
    elif player_score == dealer_score:
        balance += bet
        msg = "➖ 무승부 (베팅 반환)"
    else:
        msg = "❌ 패배"

    update_balance(user[1], balance)
    session["balance"] = balance

    return {
        "player_score": player_score,
        "dealer_score": dealer_score,
        "player_hand": " ".join(str(c) for c in player_cards),
        "dealer_hand": " ".join(str(c) for c in dealer_cards),
        "balance": balance,
        "msg": msg,
    }


# ------------------------
# 실행
# ------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
