# import streamlit as st
# from src.pdf_ingest import ingest_pdfs
# from src.generate import generate_enriched_response, SECTION_LABELS
# from src.utils import get_llm
# from langchain.chains import ConversationChain
# from langchain.memory import ConversationBufferMemory

# # ─── Page Config ─────────────────────────────────────────────────────
# st.set_page_config(page_title="NSF Section Generator", layout="wide")

# # ─── Session State Init ──────────────────────────────────────────────
# if "conversation_chain" not in st.session_state:
#     memory = ConversationBufferMemory()
#     llm = get_llm()
#     st.session_state.conversation_chain = ConversationChain(llm=llm, memory=memory)

# if "chat_history" not in st.session_state:
#     st.session_state.chat_history = []

# if "draft_generated" not in st.session_state:
#     st.session_state.draft_generated = False

# if "enriched_text" not in st.session_state:
#     st.session_state.enriched_text = ""

# if "sources" not in st.session_state:
#     st.session_state.sources = []

# if "edit_mode" not in st.session_state:
#     st.session_state.edit_mode = False

# # ─── Layout: Two Columns ─────────────────────────────────────────────
# left, right = st.columns([1, 2])

# # ─── Left: Form for User Inputs ──────────────────────────────────────
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

#     if submitted:
#         with st.spinner("Generating and validating..."):
#             enriched_text, sources = generate_enriched_response(user_inputs)

#         if enriched_text.startswith("Please fill out the form"):
#             st.warning(enriched_text)
#         else:
#             st.success("Draft complete!")
#             st.session_state.enriched_text = enriched_text
#             st.session_state.sources = sources
#             st.session_state.draft_generated = True
#             st.session_state.chat_history.clear()
#             st.session_state.conversation_chain.memory.clear()
#             st.session_state.edit_mode = False

# # ─── Right: Output, Edit, and Chat ───────────────────────────────────
# with right:
#     # ─── Show Final Draft ────────────────────────────────────────────
#     if st.session_state.enriched_text:
#         st.markdown("### Final Draft")

#         if st.session_state.edit_mode:
#             edited_text = st.text_area("Edit your draft below:",
#                                        value=st.session_state.enriched_text,
#                                        height=400,
#                                        key="edited_draft")

#             col1, col2 = st.columns(2)
#             with col1:
#                 if st.button("Save Edits"):
#                     st.session_state.enriched_text = edited_text
#                     st.session_state.edit_mode = False
#                     st.success("Edits saved and will be used in follow-up questions.")
#                     st.session_state.conversation_chain.memory.chat_memory.clear()
#                     st.session_state.conversation_chain.memory.chat_memory.add_user_message(
#                         "This is the final enriched document:\n" + edited_text
#                     )
#             with col2:
#                 if st.button("Cancel"):
#                     st.session_state.edit_mode = False
#         else:
#             st.markdown(st.session_state.enriched_text)
#             st.button("✏️ Edit Draft", on_click=lambda: st.session_state.update(edit_mode=True))

#         # ─── Sources Display ─────────────────────────────────────────
#         st.markdown("### Sources Used")
#         for s in st.session_state.sources:
#             if s.endswith(".pdf"):
#                 st.markdown(f"- {s}")
#             elif s.startswith("http"):
#                 st.markdown(f"- [Web Link]({s})")
#             else:
#                 st.markdown(f"- {s}")

#         # Add final draft context to memory (if not in edit mode)
#         if not st.session_state.edit_mode:
#             st.session_state.conversation_chain.memory.chat_memory.add_user_message(
#                 "This is the final enriched document:\n" + st.session_state.enriched_text
#             )

#     # ─── Follow-up Chat ─────────────────────────────────────────────
#     st.markdown("### Follow-up Chat")

#     if followup := st.chat_input("Ask a follow-up question..."):
#         if not st.session_state.draft_generated:
#             bot_reply = "Please fill out the form to begin generating your NSF Facilities Template."
#         else:
#             bot_reply = st.session_state.conversation_chain.predict(input=followup)
#             st.session_state.conversation_chain.memory.chat_memory.add_user_message(followup)
#             st.session_state.conversation_chain.memory.chat_memory.add_ai_message(bot_reply)

#         st.session_state.chat_history.append((followup, bot_reply))

#     # ─── Chat History Display ───────────────────────────────────────
#     for user_q, bot_a in st.session_state.chat_history:
#         st.markdown(f"**You:** {user_q}")
#         st.markdown(f"**Assistant:** {bot_a}")

import streamlit as st
from src.pdf_ingest import ingest_pdfs
from src.generate import generate_enriched_response, SECTION_LABELS
from src.utils import get_llm
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

# Page Config ────────────────────────────────
st.set_page_config(page_title="NSF Section Generator", layout="wide")

# Utility Function ───────────────────────────
def build_full_draft(sections_dict, section_labels):
    final = ""
    for section_label in section_labels:
        section_text = sections_dict.get(section_label, "").strip()
        if section_text:
            final += f"\n\n## {section_label}\n\n{section_text}\n"
    return final.strip()

# Session State Init ─────────────────────────
if "conversation_chain" not in st.session_state:
    memory = ConversationBufferMemory()
    llm = get_llm()
    st.session_state.conversation_chain = ConversationChain(llm=llm, memory=memory)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "draft_generated" not in st.session_state:
    st.session_state.draft_generated = False

if "enriched_sections" not in st.session_state:
    st.session_state.enriched_sections = {}

if "final_draft" not in st.session_state:
    st.session_state.final_draft = ""

if "sources" not in st.session_state:
    st.session_state.sources = []

# Layout ─────────────────────────────────────
left, right = st.columns([1, 2])

# Form ─────────────────────────────────
with left:
    st.title("NSF Section Form")

    if st.button("Reindex PDFs in `/data` folder"):
        ingest_pdfs()
        st.success("Reindex complete!")

    st.markdown("### Fill in the details below:")

    user_inputs = {}
    with st.form("input_form"):
        for label in SECTION_LABELS:
            user_inputs[label] = st.text_area(label, height=100)
        submitted = st.form_submit_button("Generate Section")

    if submitted:
        with st.spinner("Generating and validating..."):
            section_outputs, sources = generate_enriched_response(user_inputs)

        if not section_outputs:
            st.warning("Please fill out the form to generate your NSF Facilities Template.")
        else:
            st.session_state.enriched_sections = section_outputs
            st.session_state.final_draft = build_full_draft(section_outputs, SECTION_LABELS)
            st.session_state.sources = sources
            st.session_state.draft_generated = True

            # Clear and refresh conversation memory with new draft
            st.session_state.conversation_chain.memory.chat_memory.clear()
            st.session_state.conversation_chain.memory.chat_memory.add_user_message(
                "This is the final enriched document:\n" + st.session_state.final_draft
            )
            st.session_state.chat_history.clear()
            st.success("Draft complete!")

with right:
    if st.session_state.draft_generated:
        st.markdown("### Final Draft (Sections)")

        for section in SECTION_LABELS:
            text = st.session_state.enriched_sections.get(section, "")

            if not text:
                continue

            st.markdown(f"## {section}")

            if f"{section}_edit_mode" not in st.session_state:
                st.session_state[f"{section}_edit_mode"] = False

            if st.session_state[f"{section}_edit_mode"]:
                edited_text = st.text_area(
                    f"Edit {section}",
                    value=text,
                    height=200,
                    key=f"{section}_textarea"
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Save {section} Edits"):
                        
                        st.session_state.enriched_sections[section] = edited_text
                        st.session_state[f"{section}_edit_mode"] = False

                        st.session_state.final_draft = build_full_draft(
                            st.session_state.enriched_sections, SECTION_LABELS
                        )
                        st.session_state.conversation_chain.memory.chat_memory.clear()
                        st.session_state.conversation_chain.memory.chat_memory.add_user_message(
                            "This is the final enriched document:\n" + st.session_state.final_draft
                        )
                        st.success(f"Saved edits for {section}.")

                with col2:
                    if st.button(f"Cancel {section} Edits"):
                        st.session_state[f"{section}_edit_mode"] = False

            else:
                st.markdown(text)
                st.button(
                    f" Edit {section}",
                    key=f"{section}_edit_button",
                    on_click=lambda s=section: st.session_state.update({f"{s}_edit_mode": True})
                )

        # Sources ──────────────────────────────
        st.markdown("### Sources Used")
        for s in st.session_state.sources:
            if s.endswith(".pdf"):
                st.markdown(f"- {s}")
            elif s.startswith("http"):
                st.markdown(f"- [{s}]({s})")
            else:
                st.markdown(f"- {s}")

    # Follow-up Chat ──────────────────────────
    st.markdown("### Follow-up Chat")

    if followup := st.chat_input("Ask a follow-up question..."):
        if not st.session_state.draft_generated:
            bot_reply = "Please fill out the form to begin generating your NSF Facilities Template."
        else:
            st.session_state.conversation_chain.memory.chat_memory.clear()
            st.session_state.conversation_chain.memory.chat_memory.add_user_message(
                "This is the final enriched document:\n" + st.session_state.final_draft
            )

            bot_reply = st.session_state.conversation_chain.predict(input=followup)

            st.session_state.conversation_chain.memory.chat_memory.add_user_message(followup)
            st.session_state.conversation_chain.memory.chat_memory.add_ai_message(bot_reply)

        st.session_state.chat_history.append((followup, bot_reply))

    for user_q, bot_a in st.session_state.chat_history:
        st.markdown(f"**You:** {user_q}")
        st.markdown(f"**Assistant:** {bot_a}")
