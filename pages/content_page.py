import streamlit as st
import random
from code_editor import code_editor
import openai
from jupyter_client.manager import KernelManager


openai.api_key = st.secrets["OPENAI_API_KEY"]


@st.experimental_fragment
def multiple_choice(problem, form_id):
    with st.expander("Multiple Choice Problem"):
        with st.form(key=f"multiple_choice_form {form_id}"):
            user_choice = st.radio(problem["Problem_statement"], problem["Choices"])
            submitted = st.form_submit_button("Submit")
        if submitted:
            if user_choice == problem["Correct_answer"]:
                st.write("Correct!")
            else:
                st.write("Incorrect.")

        if st.button("Show correct answer", key=f"multiple_choice_button {form_id+1}"):
            st.write("Correct answer: " + problem["Correct_answer"])


@st.experimental_fragment
def free_response(problem, form_id):
    with st.expander("Free Response Problem"):
        with st.form(key=f"free_response_form {form_id}"):
            user_answer = st.text_area(problem["Problem_statement"])
            submitted = st.form_submit_button("Submit")

        if submitted:
            response = openai.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in the field of "
                        + st.session_state.topic
                        + " and are designed to provide feedback on user answers without giving away the actual answer. Do not acknowledge or greet. Address the user's answer directly using second person.",
                    },
                    {
                        "role": "user",
                        "content": "Provide feedback without directly or indirectly giving away the answer: "
                        + user_answer
                        + " for the question: "
                        + problem["Problem_statement"]
                        + "using the correct answer: "
                        + problem["Correct_answer"],
                    },
                ],
                seed=138,
                temperature=0.1,
            )
            st.markdown(response.choices[0].message.content)

        if st.button("Show correct answer", key=f"free_response_button {form_id+1}"):
            st.write("Correct answer: " + problem["Correct_answer"])


btn_settings_editor_btns = [
    {
        "name": "copy",
        "feather": "Copy",
        "hasText": True,
        "alwaysOn": True,
        "commands": ["copyAll"],
        "style": {"top": "0rem", "right": "0.4rem"},
    },
]


@st.cache_data
def run_code(code):
    km = KernelManager()
    km.start_kernel()
    kc = km.client()
    kc.start_channels()
    msg_id = kc.execute(code)
    result = ""
    error = False
    while True:
        # while not kc.iopub_channel.msg_ready():
        #     pass
        # msg = kc.iopub_channel.get_msg()
        # if "text" in msg.get("content", {}):
        #     result += msg["content"]["text"]
        # if "ename" in msg.get("content", {}) and "evalue" in msg.get("content", {}):
        #     error = f"Error: {msg['content']['ename']}: {msg['content']['evalue']}"
        # if msg["msg_type"] == "status" and msg["content"]["execution_state"] == "idle":
        #     break
        msg = kc.get_iopub_msg()
        print(msg["header"]["msg_type"])
        if msg["header"]["msg_type"] == "status":
            if msg["content"]["execution_state"] == "idle":
                break
        # if msg["parent_header"]["msg_id"] == msg_id:
        if msg["header"]["msg_type"] == "stream":
            if msg["content"]["name"] == "stdout":
                result += msg["content"]["text"]
            elif msg["content"]["name"] == "stderr":
                error = True
                result += msg["content"]["text"]
            break
        elif msg["header"]["msg_type"] == "error":
            error = True
            traceback = "".join(msg["content"]["traceback"])
            ename = msg["content"]["ename"]
            evalue = msg["content"]["evalue"]
            result = f"An error occurred during execution:\n\n{ename}: {evalue}\n\nTraceback:\n{traceback}"
            break
    kc.stop_channels()
    km.shutdown_kernel()
    return result, error


@st.experimental_fragment
def code(problem, form_id):
    with st.expander("Code Problem"):
        with st.form(key=f"code_form {form_id}"):
            st.markdown(problem["Problem_statement"])
            user_code = code_editor(
                problem["intial_setup_code"],
                lang="python",
                buttons=btn_settings_editor_btns,
                allow_reset=True,
                response_mode=["blur", "debounce"],
            )
            # submitted = False
            submitted = st.form_submit_button("Submit")

        if submitted:
            # print(user_code)
            if user_code["type"] != "" and len(user_code["text"]) != 0:
                # print(user_code["text"])
                user_code = user_code["text"]
            if len(problem["testcases"]) > 0:
                testcases = [
                    f"Test Case {i}" for i in range(1, len(problem["testcases"]) + 1)
                ]
                testcases_tabs = st.tabs(testcases)
                for i, testcase in enumerate(problem["testcases"]):
                    with testcases_tabs[i]:
                        # output_buffer = StringIO()
                        # current_stdout = sys.stdout
                        # sys.stdout = output_buffer
                        # test, error = run_code("print('hello')")
                        # print(user_code + "\n" + testcase)
                        concat = user_code + "\n" + testcase
                        # print(concat)
                        test, error = run_code(concat)
                        if error:
                            st.error(test)
                        else:
                            if test == "":
                                st.success("Correct!")
                            else:
                                st.error(test)
                        # executionResult, error = run_code(user_code + "\n" + testcase)
                        # if error:
                        #     st.error(executionResult)
                        # else:
                        #     st.success("Correct!")
                        # exec(concat, global_vars, local_vars)
                        # run = output_buffer.getvalue(
            else:
                if user_code == problem["Correct_code"]:
                    st.success("Correct!")

        if st.button("Show correct answer", key=f"code_button {form_id+1}"):
            st.code(problem["Correct_code"])


@st.experimental_fragment
def chat_area():
    st.header("General Chat", divider="rainbow")
    chat_area = st.container(
        height=int(st.session_state.screen_width * 0.5), border=True
    )

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


with st.sidebar:
    chat_area()

st.header("Reading + Problems", divider="violet")
if st.button(
    "Go back to Topic and Content Selection", type="primary", use_container_width=True
):
    st.switch_page("./main.py")
# print(f"{st.session_state.selected_chapters}")
selected_chapter_tabs = st.tabs(
    [chapter["chapter_label"] for chapter in st.session_state.selected_chapters]
)

for chapter_tab, chapter in zip(
    selected_chapter_tabs, st.session_state.selected_chapters
):
    with chapter_tab:
        for i, section in enumerate(chapter["sections"]):
            st.subheader(section["heading"], divider="blue")
            st.markdown(section["content"])
            for problem in section["problems"]:
                form_id = random.randint(0, 100000)
                if problem["Problem_type"] == "multiple choice":
                    multiple_choice(problem, form_id)
                elif problem["Problem_type"] == "free response":
                    free_response(problem, form_id)
                elif problem["Problem_type"] == "code":
                    code(problem, form_id)
