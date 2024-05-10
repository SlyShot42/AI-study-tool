import streamlit as st
import openai

st.title('Prompt Study Tool')

client = openai.Client(api_key=st.secrets["OPENAI_API_KEY"])

if "openai_model" not in st.session_state:
    st.session_state.openai_model = "gpt-3.5-turbo"
    
if "messages" not in st.session_state:
    st.session_state.messages = []
    


st.header("Topic:", divider="violet")
topic = st.text_area("Enter the topic you want to study", key="topic")


st.header("Reading + Problems", divider="violet")
st.markdown("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Fusce sed consectetur urna, quis mollis erat. Vestibulum congue velit non aliquam ullamcorper. Proin arcu nibh, varius id finibus at, iaculis sit amet diam. Donec arcu tellus, semper at vestibulum id, ultricies eget ex. Proin egestas tempor metus, lobortis laoreet lacus congue id. Aenean luctus mauris id feugiat varius. Aenean nisl ex, aliquet id molestie non, ornare congue nulla. Vestibulum euismod, nisi eget lacinia pretium, nunc metus bibendum magna, eu ullamcorper ex lectus vel enim.")

with st.sidebar:
    chat_area = st.container(height=800, border=True)
    
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
                stream = client.chat.completions.create(
                    model=st.session_state["openai_model"],
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                    stream=True,
                )
                response = st.write_stream(stream)
            st.session_state.messages.append({"role": "assistant", "content": response})
    
# if prompt := st.chat_input("What is up?"):
#     st.session_state.messages.append({"role": "user", "content": prompt})
#     with st.chat_message("user"):
#         st.markdown(prompt)
