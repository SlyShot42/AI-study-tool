import streamlit as st
import json
from streamlit_js_eval import streamlit_js_eval
import openai

st.title('Prompt Study Tool')

openai.api_key = st.secrets["OPENAI_API_KEY"]

if "openai_model" not in st.session_state:
    st.session_state.openai_model = "gpt-3.5-turbo"
    
if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "topic" not in st.session_state:
    st.session_state.topic = ""

if "chapter_numbers" not in st.session_state:
    st.session_state.chapter_numbers = []

st.header("Topic:", divider="violet")
if topic := st.text_area("Enter the topic you want to study"):
    st.session_state.topic = topic
    response = openai.chat.completions.create(
        model=st.session_state["openai_model"],
        response_format={ 'type': 'json_object'},
        messages=[
            {"role": "system", "content": "You are a course textbook writing expert designed to output in JSON."},
            {"role": "user", "content": "Generate the table of contents (include chapter and sections) for a textbook on " + st.session_state.topic + "."},
        ],
        seed=138,
        temperature=0.1,
    )
    data = json.loads(response.choices[0].message.content)
    print(data)
    chapters = data['table_of_contents']['chapters']
    st.session_state.chapter_numbers = [str(chapter['chapter_number']) + ': ' + chapter['chapter_title'] for chapter in chapters]
    print(st.session_state.chapter_numbers)

    st.header("Reading + Problems", divider="violet")
    chapter_tabs = st.tabs(st.session_state.chapter_numbers)
    for chapter_tab, chapter in zip(chapter_tabs, chapters):
        with chapter_tab:
            for section in chapter['sections']:
                st.subheader(section)
                st.markdown("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Fusce sed consectetur urna, quis mollis erat. Vestibulum congue velit non aliquam ullamcorper. Proin arcu nibh, varius id finibus at, iaculis sit amet diam. Donec arcu tellus, semper at vestibulum id, ultricies eget ex. Proin egestas tempor metus, lobortis laoreet lacus congue id. Aenean luctus mauris id feugiat varius. Aenean nisl ex, aliquet id molestie non, ornare congue nulla. Vestibulum euismod, nisi eget lacinia pretium, nunc metus bibendum magna, eu ullamcorper ex lectus vel enim.")

with st.sidebar:
    st.header("General Chat", divider="rainbow")
    chat_area = st.container(height=int(streamlit_js_eval(js_expressions='screen.height', key = 'SCR')*0.5),border=True)
    
    for message in st.session_state.messages:
        with chat_area:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    #     with chat_message_placeholder.chat_message(message["role"]):
    #         chat_message_placeholder.markdown(message["content"])
    if prompt := st.chat_input("hello there"): 
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_area:
            with st.chat_message("user"):
                st.markdown(prompt)
                
            with st.chat_message("assistant"):
                stream = openai.chat.completions.create(
                    model=st.session_state["openai_model"],
                    messages=st.session_state.messages,
                    stream=True,
                )
                response = st.write_stream(stream)
            st.session_state.messages.append({"role": "assistant", "content": response})
    
# if prompt := st.chat_input("What is up?"):
#     st.session_state.messages.append({"role": "user", "content": prompt})
#     with st.chat_message("user"):
#         st.markdown(prompt)
