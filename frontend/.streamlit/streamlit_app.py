import json, urllib.parse, time, requests, os
import streamlit as st

# =========================
# CẤU HÌNH
# =========================
BACKEND_URL = os.getenv("BACKEND_URL", "https://<YOUR_BACKEND_HOST>")

st.set_page_config(page_title="Telegram Mini App (Streamlit)", layout="wide")
st.title("Telegram Mini App – Streamlit Frontend")

# --- Nhúng JS Telegram SDK và lấy initData ---
# Ý tưởng: lần đầu vào, nếu URL chưa có ?initData=... thì JS sẽ:
# 1) đọc window.Telegram.WebApp.initData
# 2) redirect cùng URL + ?initData=... để Streamlit (Python) đọc được
telegram_script = """
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<script>
(function() {
  try {
    const tg = window.Telegram.WebApp;
    tg.expand();

    // Nếu URL CHƯA có initData thì thêm vào
    const url = new URL(window.location.href);
    if (!url.searchParams.get("initData")) {
      const initData = tg.initData || "";
      // Optional: thêm start_param -> Python có thể lấy bằng initDataUnsafe.start_param
      url.searchParams.set("initData", encodeURIComponent(initData));
      window.location.replace(url.toString());
    }
  } catch(e) {
    console.error("Init Telegram failed", e);
  }
})();
</script>
"""
st.markdown(telegram_script, unsafe_allow_html=True)

# Đọc initData từ query string
query_params = st.query_params
init_data_encoded = query_params.get("initData", [""])[0] if isinstance(query_params.get("initData", ""), list) else query_params.get("initData", "")
# vì ở script đã encodeURIComponent 2 lần (SDK -> URL), ta decode 1 lần
try:
    init_data = urllib.parse.unquote(init_data_encoded)
except:
    init_data = init_data_encoded

with st.expander("Debug initData (raw)"):
    st.code(init_data or "NO_INIT_DATA", language="text")

# Gọi API backend verify initData
col1, col2 = st.columns(2)
with col1:
    if st.button("✅ Verify initData với Backend"):
        if not init_data:
            st.error("Chưa có initData (mở từ Telegram Bot để có).")
        else:
            try:
                r = requests.post(f"{BACKEND_URL}/verify-init", json={"initData": init_data}, timeout=10)
                data = r.json()
                if data.get("ok"):
                    st.success("Hợp lệ ✅")
                else:
                    st.error("Không hợp lệ ❌: " + str(data.get("error", "")))
            except Exception as e:
                st.error(f"Lỗi gọi backend: {e}")

with col2:
    note = st.text_input("Nhập ghi chú gửi về Bot (sendData)")
    # Nút gọi tg.sendData bằng JS
    send_js = f"""
    <script>
    function sendData() {{
      try {{
        const tg = window.Telegram.WebApp;
        const payload = {{
          type: 'note', text: {json.dumps(note)}, ts: Date.now()
        }};
        tg.sendData(JSON.stringify(payload));
        tg.HapticFeedback.impactOccurred('light');
      }} catch(e) {{
        alert('Không phải Telegram WebApp hoặc lỗi: ' + e);
      }}
    }}
    </script>
    <button onclick="sendData()">Gửi về Bot (sendData)</button>
    """
    st.markdown(send_js, unsafe_allow_html=True)

st.info("👉 Hãy mở Mini App từ Bot (Menu hoặc deep-link) để có `initData`. Sau đó bấm Verify.")

st.divider()
st.caption("Demo: Streamlit nhận initData qua JS → query params → Python; gửi data cho Bot bằng tg.sendData().")
