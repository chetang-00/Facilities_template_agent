# import streamlit as st
# from src.pdf_ingest import ingest_pdfs
# from src.generate import generate_enriched_response, SECTION_LABELS

# st.set_page_config(page_title="NSF Section Generator", layout="wide")
# st.title("📄 NSF Facilities Section Generator with PDF Validation")

# if st.button("🔁 Reindex PDFs in `/data` folder"):
#     ingest_pdfs()
#     st.success("Reindex complete!")

# st.markdown("### ✍️ Fill in the details below:")

# user_inputs = {}
# with st.form("input_form"):
#     for label in SECTION_LABELS:
#         user_inputs[label] = st.text_area(label, height=150)
#     submitted = st.form_submit_button("Generate Section")

# if submitted:
#     with st.spinner("Generating and validating..."):
#         enriched_text, sources = generate_enriched_response(user_inputs)
#     st.success("✅ Draft complete!")
#     st.markdown("### 📝 Final Draft")
#     st.markdown(enriched_text)

#     st.markdown("### 📚 Sources Used")
#     for s in sources:
#         st.markdown(f"- {s}")

#     # Optional follow-up chat
#     st.markdown("### 💬 Follow-up Chat")
#     followup = st.text_input("Ask a follow-up question:")
#     if followup:
#         from src.utils import get_llm
#         llm = get_llm()
#         st.write(llm.invoke(f"{followup}\n\nReference the previous document: \n{enriched_text}"))

"----------------------------------------------------------------------------"
# import streamlit as st
# from src.pdf_ingest import ingest_pdfs
# from src.generate import generate_enriched_response, SECTION_LABELS
# from src.utils import get_llm
# from langchain.chains import ConversationChain
# from langchain.memory import ConversationBufferMemory

# # Initialize session state for conversation
# if "conversation_chain" not in st.session_state:
#     memory = ConversationBufferMemory()
#     llm = get_llm()
#     st.session_state.conversation_chain = ConversationChain(llm=llm, memory=memory)

# if "chat_history" not in st.session_state:
#     st.session_state.chat_history = []

# st.set_page_config(page_title="NSF Section Generator", layout="wide")

# # Split the page into two columns
# left, right = st.columns([1, 2])

# with left:
#     st.title("NSF Section Form")

#     if st.button("Reindex PDFs in `/data` folder"):
#         ingest_pdfs()
#         st.success("Reindex complete!")

#     st.markdown("### ✍️ Fill in the details below:")

#     user_inputs = {}
#     with st.form("input_form"):
#         for label in SECTION_LABELS:
#             user_inputs[label] = st.text_area(label, height=100)
#         submitted = st.form_submit_button("Generate Section")

# if submitted:
#     with right:
#         with st.spinner("Generating and validating..."):
#             enriched_text, sources = generate_enriched_response(user_inputs)
#         st.success("Draft complete!")
#         st.markdown("### Final Draft")
#         st.markdown(enriched_text)

#         st.markdown("### Sources Used")
#         for s in sources:
#             if s.endswith(".pdf"):
#                 st.markdown(f"- {s}")
#             elif s.startswith("http"):
#                 st.markdown(f"- [Web Link]({s})")
#             else:
#                 st.markdown(f"- {s}")


#         st.session_state.conversation_chain.memory.chat_memory.add_user_message(
#             "This is the final enriched document:" + enriched_text
#         )

# with right:
#     st.markdown("### Follow-up Chat")
#     followup = st.text_input("Ask a follow-up question:", key="followup_input")

#     if followup:
#         response = st.session_state.conversation_chain.predict(input=followup)
#         st.session_state.chat_history.append((followup, response))

#     for i, (user_q, bot_a) in enumerate(st.session_state.chat_history):
#         st.markdown(f"**You:** {user_q}")
#         st.markdown(f"**Assistant:** {bot_a}")

import streamlit as st
from src.pdf_ingest import ingest_pdfs
from src.generate import generate_enriched_response, SECTION_LABELS
from src.utils import get_llm
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

# ─── Page Config ─────────────────────────────────────────────────────
st.set_page_config(page_title="NSF Section Generator", layout="wide")

# ─── Session State Init ──────────────────────────────────────────────
if "conversation_chain" not in st.session_state:
    memory = ConversationBufferMemory()
    llm = get_llm()
    st.session_state.conversation_chain = ConversationChain(llm=llm, memory=memory)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "draft_generated" not in st.session_state:
    st.session_state.draft_generated = False

if "enriched_text" not in st.session_state:
    st.session_state.enriched_text = ""

if "sources" not in st.session_state:
    st.session_state.sources = []

# ─── Layout: Two Columns ─────────────────────────────────────────────
left, right = st.columns([1, 2])

with left:
    st.title("NSF Section Form")

    if st.button("Reindex PDFs in `/data` folder"):
        ingest_pdfs()
        st.success("Reindex complete!")

    st.markdown("### ✍️ Fill in the details below:")

    user_inputs = {}
    with st.form("input_form"):
        for label in SECTION_LABELS:
            user_inputs[label] = st.text_area(label, height=100)
        submitted = st.form_submit_button("Generate Section")

    if submitted:
        with st.spinner("Generating and validating..."):
            enriched_text, sources = generate_enriched_response(user_inputs)

        if enriched_text.startswith("Please fill out the form"):
            st.warning(enriched_text)
        else:
            st.success(" Draft complete!")
            st.session_state.enriched_text = enriched_text
            st.session_state.sources = sources
            st.session_state.draft_generated = True
            st.session_state.chat_history.clear()
            st.session_state.conversation_chain.memory.clear()

with right:
    # ─── Show Generated Content ─────────────────────────────────────
    if st.session_state.enriched_text:
        st.markdown("### Final Draft")
        st.markdown(st.session_state.enriched_text)

        st.markdown("### Sources Used")
        for s in st.session_state.sources:
            if s.endswith(".pdf"):
                st.markdown(f"- {s}")
            elif s.startswith("http"):
                st.markdown(f"- [Web Link]({s})")
            else:
                st.markdown(f"- {s}")

        st.session_state.conversation_chain.memory.chat_memory.add_user_message(
            "This is the final enriched document:" + st.session_state.enriched_text
        )

    # ─── Chat Section ──────────────────────────────────────────────
    st.markdown("###  Follow-up Chat")

    if followup := st.chat_input("Ask a follow-up question..."):
        if not st.session_state.draft_generated:
            bot_reply = " Hello! Please fill out the form to begin generating your NSF Facilities Template."
        else:
            bot_reply = st.session_state.conversation_chain.predict(input=followup)
            st.session_state.conversation_chain.memory.chat_memory.add_user_message(followup)
            st.session_state.conversation_chain.memory.chat_memory.add_ai_message(bot_reply)

        st.session_state.chat_history.append((followup, bot_reply))

    # Always show chat history
    for user_q, bot_a in st.session_state.chat_history:
        st.markdown(f"**You:** {user_q}")
        st.markdown(f"**Assistant:** {bot_a}")

