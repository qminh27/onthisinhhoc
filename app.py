import json
import random
from pathlib import Path

import streamlit as st

TITLE = "📚 MYMYMYMYMYMYMY"
BASE = Path(__file__).parent

st.set_page_config(page_title="Ôn tập Sinh", page_icon="📚", layout="centered")


@st.cache_data
def load_data():
    with open(BASE / "questions.json", encoding="utf-8") as f:
        return json.load(f)


DATA = load_data()
MCQ = {q["n"]: q for q in DATA["mcq"]}
TF = {q["n"]: q for q in DATA["tf"]}

S = st.session_state
S.setdefault("phase", "home")  # home | exam | result | review


def md(text):
    return text.replace("$", "\\$").replace("\n", "  \n")


def show_img(name):
    if name:
        st.image(str(BASE / "images" / name))


def ans_text(flag):
    return "Đúng" if flag else "Sai"


# ---------------------------------------------------------------- logic
def start(shuffle):
    for key in list(S.keys()):
        if key.startswith(("mcq-", "tf-")):
            del S[key]
    mcq_order, tf_order = sorted(MCQ), sorted(TF)
    if shuffle:
        random.shuffle(mcq_order)
        random.shuffle(tf_order)
    S.mcq_order, S.tf_order = mcq_order, tf_order
    S.phase = "exam"


def submit():
    # chụp lại toàn bộ đáp án đang chọn (None = chưa làm)
    S.ans = {
        "mcq": {n: S.get(f"mcq-{n}") for n in S.mcq_order},
        "tf": {n: {k: S.get(f"tf-{n}-{k}") for k in "abcd"} for n in S.tf_order},
    }
    S.phase = "result"


def mcq_status(n):
    pick = S.ans["mcq"][n]
    if pick is None:
        return "blank"
    return "ok" if pick == MCQ[n]["ans"] else "wrong"


def tf_status(n):
    picks = S.ans["tf"][n]
    if all(v is None for v in picks.values()):
        return "blank"
    full = all(picks[k] == ans_text(TF[n]["ans"][k]) for k in "abcd")
    return "ok" if full else "wrong"


# ---------------------------------------------------------------- pages
def page_home():
    st.title(TITLE)
    c1, c2 = st.columns([2, 1])
    shuffle = c1.checkbox("Xáo trộn thứ tự câu")
    if c2.button("🚀 Bắt đầu", type="primary", use_container_width=True):
        start(shuffle)
        st.rerun()
    st.info(
        f"Bấm **Bắt đầu** để làm bài ({len(MCQ)} câu trắc nghiệm + {len(TF)} câu đúng/sai)."
    )


def page_exam():
    # nút Nộp bài cố định góc trên bên phải
    st.markdown(
        """
        <style>
        .st-key-submit_btn {
            position: fixed; top: 3.75rem; right: 1.5rem;
            width: auto !important; z-index: 1000;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    if st.button("📤 Nộp bài", key="submit_btn", type="primary"):
        submit()
        st.rerun()

    st.title(TITLE)

    st.subheader("Phần I. Trắc nghiệm")
    for i, n in enumerate(S.mcq_order, 1):
        q = MCQ[n]
        with st.container(border=True):
            st.markdown(f"**Câu {i}.** " + md(q["q"]))
            show_img(q["img"])
            st.radio(
                f"Câu {i}", list(q["opts"]), index=None, key=f"mcq-{n}",
                format_func=lambda k, q=q: f"{k}. {q['opts'][k]}",
                label_visibility="collapsed",
            )

    st.subheader("Phần II. Đúng / Sai")
    for i, n in enumerate(S.tf_order, 1):
        q = TF[n]
        with st.container(border=True):
            st.markdown(f"**Câu {i}.** " + md(q["stem"]))
            show_img(q["img"])
            for k in "abcd":
                st.markdown(f"**{k})** " + md(q["stmts"][k]))
                st.radio(
                    f"{i}{k}", ["Đúng", "Sai"], index=None, horizontal=True,
                    key=f"tf-{n}-{k}", label_visibility="collapsed",
                )


def page_result():
    st.title(TITLE)
    st.header("Kết quả")

    m_stat = [mcq_status(n) for n in S.mcq_order]
    t_stat = [tf_status(n) for n in S.tf_order]
    total = len(m_stat) + len(t_stat)
    ok = m_stat.count("ok") + t_stat.count("ok")
    wrong = total - ok
    blank = m_stat.count("blank") + t_stat.count("blank")

    c1, c2 = st.columns(2)
    c1.metric("✅ Số câu đúng", f"{ok}/{total}")
    c2.metric("❌ Số câu sai", f"{wrong}/{total}")
    st.caption(
        f"Trắc nghiệm: {m_stat.count('ok')}/{len(m_stat)} đúng • "
        f"Đúng/sai: {t_stat.count('ok')}/{len(t_stat)} câu (đúng đủ cả 4 ý) • "
        f"Câu chưa làm (tính là sai): {blank}"
    )

    b1, b2 = st.columns(2)
    if b1.button("📖 Xem lại bài làm", type="primary", use_container_width=True):
        S.phase = "review"
        st.rerun()
    if b2.button("🔁 Làm lại", use_container_width=True):
        S.phase = "home"
        st.rerun()


def page_review():
    st.title(TITLE)
    if st.button("⬅️ Về kết quả"):
        S.phase = "result"
        st.rerun()

    icon = {"ok": "✅ Đúng", "wrong": "❌ Sai", "blank": "⚪ Chưa làm"}

    st.subheader("Phần I. Trắc nghiệm")
    for i, n in enumerate(S.mcq_order, 1):
        q, pick = MCQ[n], S.ans["mcq"][n]
        with st.container(border=True):
            st.markdown(f"**Câu {i}.** {icon[mcq_status(n)]}")
            st.markdown(md(q["q"]))
            show_img(q["img"])
            for k, text in q["opts"].items():
                line = md(f"{k}. {text}")
                if k == q["ans"]:
                    st.success(line + ("  ✔ Đáp án đúng (bạn chọn)" if k == pick else "  ✔ Đáp án đúng"))
                elif k == pick:
                    st.error(line + "  ✖ Bạn chọn")
                else:
                    st.markdown(line)

    st.subheader("Phần II. Đúng / Sai")
    for i, n in enumerate(S.tf_order, 1):
        q = TF[n]
        with st.container(border=True):
            st.markdown(f"**Câu {i}.** {icon[tf_status(n)]}")
            st.markdown(md(q["stem"]))
            show_img(q["img"])
            for k in "abcd":
                pick = S.ans["tf"][n][k]
                right = ans_text(q["ans"][k])
                mark = "⚪" if pick is None else ("✅" if pick == right else "❌")
                st.markdown(f"{mark} **{k})** " + md(q["stmts"][k]))
                st.caption(f"Bạn chọn: {pick or 'chưa làm'} • Đáp án: {right}")

    if st.button("⬅️ Về kết quả", key="back_bottom"):
        S.phase = "result"
        st.rerun()


{"home": page_home, "exam": page_exam, "result": page_result, "review": page_review}[S.phase]()
