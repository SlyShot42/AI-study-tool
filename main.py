import streamlit as st
import traceback
import sys
from io import StringIO
import json
import random
from code_editor import code_editor
from streamlit_js_eval import streamlit_js_eval
import openai

st.title("Prompt Study Tool")

openai.api_key = st.secrets["OPENAI_API_KEY"]

if "openai_model" not in st.session_state:
    st.session_state.openai_model = "gpt-3.5-turbo"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "topic" not in st.session_state:
    st.session_state.topic = ""

if "chapter_numbers" not in st.session_state:
    st.session_state.chapter_numbers = []


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
    {
        "name": "update",
        "feather": "RefreshCw",
        "primary": True,
        "hasText": True,
        "showWithIcon": True,
        "commands": ["submit"],
        "style": {"bottom": "0rem", "right": "0.4rem"},
    },
]


@st.experimental_fragment
def code(problem, form_id):
    with st.expander("Code Problem"):
        with st.form(key=f"code_form {form_id}"):
            st.markdown(problem["Problem_statement"])
            user_code = code_editor(
                problem["intial_setup_code"],
                lang="python",
                buttons=btn_settings_editor_btns,
            )
            submitted = False
            if user_code["type"] == "submit" and len(user_code["text"]) != 0:
                # print(user_code["text"])
                user_code = user_code["text"]
            submitted = st.form_submit_button("Submit")

        if submitted and user_code != "":
            # print(user_code)
            testcases = [f"Test Case {i}" for i in range(len(problem["testcases"]))]
            testcases_tabs = st.tabs(testcases)
            for i, testcase in enumerate(problem["testcases"]):
                with testcases_tabs[i]:
                    # output_buffer = StringIO()
                    # current_stdout = sys.stdout
                    # sys.stdout = output_buffer
                    try:
                        print(user_code + "\n" + testcase)
                        concat = user_code + "\n" + testcase
                        local_vars = {}
                        global_vars = {"__builtins__": __builtins__}
                        # exec('assert False', global_vars, local_vars)
                        exec(concat, global_vars, local_vars)
                        # run = output_buffer.getvalue()
                    except Exception as e:
                        print("Error")
                        print(e)
                        st.code(traceback.format_exc())
                        continue
                    # finally:
                    #     sys.stdout = current_stdout
                    print("success")
                    st.code("Success")

        if st.button("Show correct answer", key=f"code_button {form_id+1}"):
            st.code(problem["Correct_code"])


# if st.button("Clear"):
#     st.write("Clearing state...")

# @st.experimental_fragment
# def test():
#     with st.expander("Test"):
#         if st.button("Test"):
#             st.write("Test")

# test()
st.header("Topic:", divider="violet")
topic = st.text_area("Enter the topic you want to study")
screen_width = streamlit_js_eval(js_expressions="screen.height", key="SCR")
if topic != st.session_state.topic and topic is not None and topic != "":
    st.session_state.topic = topic
    example = r"""{
        "table_of_contents": {
            "chapters": [
                {
                    "chapter_number": 1, 
                    "chapter_title": "Introduction", 
                    "sections": [
                        "1.1 Section Title", 
                        "1.2 Section Title", 
                        "1.3 Section Title"
                    ]
                }, 
                {
                    "chapter_number": 2, 
                    "chapter_title": "Chapter 2", 
                    "sections": [
                        "2.1 Section Title", 
                        "2.2 Section Title", 
                        "2.3 Section Title"
                    ]
                }, 
                {
                    "chapter_number": 3, 
                    "chapter_title": "Chapter 3", 
                    "sections": [
                        "3.1 Section Title", 
                        "3.2 Section Title", 
                        "3.3 Section Title"
                    ]
                }
            ]
        }
    }"""
    response = openai.chat.completions.create(
        model=st.session_state["openai_model"],
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "You are a course textbook writing expert designed to output in JSON following the format: "
                + example,
            },
            {
                "role": "user",
                "content": "Generate the table of contents (include chapter and sections) for a textbook on "
                + st.session_state.topic
                + ".",
            },
        ],
        seed=138,
        temperature=0.1,
    )
    # print(response.choices[0].message.content)
    data = json.loads(response.choices[0].message.content)
    chapters = data["table_of_contents"]["chapters"]
    st.session_state.chapter_numbers = [
        str(chapter["chapter_number"]) + ": " + chapter["chapter_title"]
        for chapter in chapters
    ]
    # print(st.session_state.chapter_numbers)

    st.header("Reading + Problems", divider="violet")
    chapter_tabs = st.tabs(st.session_state.chapter_numbers)
    for chapter_tab, chapter in zip(chapter_tabs, chapters):
        with chapter_tab:
            for section in chapter["sections"]:
                st.subheader(section, divider="red")
                section_content = openai.chat.completions.create(
                    model=st.session_state["openai_model"],
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a course textbook content generation machine designed to output in markdown(surround inline latex with $..$ and display latex with $$..$$). Do not acknowledge or greet. Output the content only. Expand on information where appropriate.",
                        },
                        {
                            "role": "user",
                            "content": "Generate the content of the section (do not include section title in reponse): "
                            + section
                            + " in the"
                            + st.session_state.topic
                            + " textbook.",
                        },
                    ],
                    temperature=0.4,
                )
                # print(section_content.choices[0].message.content)
                raw_content = section_content.choices[0].message.content
                st.markdown(raw_content)

                # problem types: multiple choice, free response, code
                output_example = r"""{
                    Problems: [
                        {
                            Problem_type: "multiple choice",
                            Problem_statement: "What is the capital of France?",
                            Choices: ["Paris", "London", "Berlin", "Madrid"],
                            Correct_answer: "Paris"
                        },
                        {
                            Problem_type: "free response",
                            Problem_statement: "Who is Elon Musk?",
                            Correct_answer: "Elon Musk is the CEO of Tesla."
                        },
                        {
                            Problem_type: "code",
                            Problem_statement: "Write a function that returns the sum of two numbers...(include any and all necessary information for the user to understand the problem along with the function signatures and global variables, if any, to be used in the test cases)",
                            intial_setup_code: "def add(a, b): \n\t# your code here",
                            testcases: [
                                "assert add(1, 2) == 3",
                                "assert add(0, 0) == 0",
                                "assert add(-1, 1) == 0"
                                ],
                            Correct_code: "def add(a, b):\n    return a + b"
                        }
                    ]
                }"""
                problem_content = openai.chat.completions.create(
                    model=st.session_state["openai_model"],
                    response_format={"type": "json_object"},
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a course textbook problem generation machine designed to output in JSON in the format: "
                            + output_example
                            + "Follow the problem type formatting exactly and using markdown(surround any inline latex math expressions with $..$ and display latex math expressions with $$..$$) for problem_statement field. Python is the language for any code problems. Do not put the answer/correct code of the question in the intial_setup_code field. intial_setup_code field is to contain only setup code for the problem and nothing else. Make sure that testcases can run successfully with the intial_setup_code and the correct code provided.",
                        },
                        {
                            "role": "user",
                            "content": "Generate exactly 2 problems of random types for the section: "
                            + section
                            + "referencing the section content"
                            + raw_content,
                        },
                    ],
                    seed=138,
                    temperature=0.4,
                )
                # print(problem_content.choices[0].message.content)
                problems = json.loads(problem_content.choices[0].message.content)
                problems = problems["Problems"]
                for problem in problems:
                    form_id = random.randint(0, 100000)
                    if problem["Problem_type"] == "multiple choice":
                        multiple_choice(problem, form_id)
                    elif problem["Problem_type"] == "free response":
                        free_response(problem, form_id)
                    elif problem["Problem_type"] == "code":
                        code(problem, form_id)

    with st.sidebar:
        st.header("General Chat", divider="rainbow")
        chat_area = st.container(height=int(screen_width * 0.5), border=True)

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
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )

# if prompt := st.chat_input("What is up?"):
#     st.session_state.messages.append({"role": "user", "content": prompt})
#     with st.chat_message("user"):
#         st.markdown(prompt)
