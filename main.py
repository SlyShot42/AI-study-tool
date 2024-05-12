import streamlit as st
import json
import random
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


@st.experimental_fragment
def code(problem, form_id):
    with st.expander("Code Problem"):
        st.write(problem["Problem_statement"])
        st.write("Correct code: " + problem["Correct_code"])

        if st.button("Show correct answer", key=f"code_button {form_id+1}"):
            st.write("Correct answer: " + problem["Correct_answer"])


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
    example = '{"table_of_contents": {"chapters": [{"chapter_number": 1, "chapter_title": "Introduction", "sections": ["1.1 Section Title", "1.2 Section Title", "1.3 Section Title"]}, {"chapter_number": 2, "chapter_title": "Chapter 2", "sections": ["2.1 Section Title", "2.2 Section Title", "2.3 Section Title"]}, {"chapter_number": 3, "chapter_title": "Chapter 3", "sections": ["3.1 Section Title", "3.2 Section Title", "3.3 Section Title"]}]}}'
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
    print(response.choices[0].message.content)
    data = json.loads(response.choices[0].message.content)
    chapters = data["table_of_contents"]["chapters"]
    st.session_state.chapter_numbers = [
        str(chapter["chapter_number"]) + ": " + chapter["chapter_title"]
        for chapter in chapters
    ]
    print(st.session_state.chapter_numbers)

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
                print(section_content.choices[0].message.content)
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
                            Problem_type: "Python code",
                            Problem_statement: "Write a function that returns the sum of two numbers",
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
                            + "Follow the problem type formatting exactly and using markdown(surround any inline latex math expressions with $..$ and display latex math expressions with $$..$$) for problem_statement field.",
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
                print(problem_content.choices[0].message.content)
                problems = json.loads(problem_content.choices[0].message.content)
                problems = problems["Problems"]
                for problem in problems:
                    form_id = random.randint(0, 100000)
                    if problem["Problem_type"] == "multiple choice":
                        multiple_choice(problem, form_id)
                    elif problem["Problem_type"] == "free response":
                        free_response(problem, form_id)
                    elif problem["Problem_type"] == "Python code":
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
