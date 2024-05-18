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
    st.session_state.openai_model = "gpt-4o"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "topic" not in st.session_state:
    st.session_state.topic = ""

if "chapters" not in st.session_state:
    st.session_state.chapters = []

if "selected_chapters" not in st.session_state:
    st.session_state.selected_chapters = []


if "screen_width" not in st.session_state:
    st.session_state.screen_width = 0


st.session_state.screen_width = streamlit_js_eval(
    js_expressions="screen.height", key="SCR"
)


@st.cache_data
def generate_content(selected_chapters):
    for chapter in selected_chapters:
        for i, section in enumerate(chapter["sections"]):
            section_content = openai.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=[
                    {
                        "role": "system",
                        "content": "You are a course textbook content generation machine designed to output in markdown(surround inline latex with $..$ and display latex with $$..$$). Do not acknowledge or greet. Output the content only. Expand on information where appropriate.",
                    },
                    {
                        "role": "user",
                        "content": "Generate the content of the section (do not include section title in reponse): \n"
                        + section
                        + "\n in the\n"
                        + st.session_state.topic
                        + "\n textbook.",
                    },
                ],
                temperature=0.4,
            )
            raw_content = section_content.choices[0].message.content

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
                        Problem_statement: "Complete the function add(a,b) that returns the sum of two numbers",
                        intial_setup_code: "def add(a, b): \n\t# your code here",
                    }
                ]
            }"""
            problem_content = openai.chat.completions.create(
                model=st.session_state["openai_model"],
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": "You are a course textbook problem generation machine designed to output in JSON in the format: \n"
                        + output_example
                        + "\nFollow the problem type formatting exactly and using markdown(surround any inline latex math expressions with $..$ and display latex math expressions with $$..$$) for problem_statement field. Python is the language for any code problems. Intial_setup_code field is to contain only setup code for the problem and nothing else. For the problem_statement, include any and all necessary information for the user to understand the problem along with the functions and variables to be used in the testcases. LEAVE NO ROOM FOR AMBIGUITY.",
                    },
                    {
                        "role": "user",
                        "content": "Generate exactly 2 problems of random types for the section: \n"
                        + section
                        + "\nreferencing the section content\n"
                        + raw_content,
                    },
                ],
                seed=138,
                temperature=0.2,
            )
            problems = json.loads(problem_content.choices[0].message.content)

            for problem in problems["Problems"]:
                if problem["Problem_type"] == "code":
                    output_example = r"""{
                        Correct_code: "def add(a, b): \n\treturn a + b",
                        testcases: [
                            "assert add(1, 2) == 3",
                            "assert add(3, 4) == 7",
                            "assert add(5, 6) == 11"
                        ],
                    }"""
                    response = openai.chat.completions.create(
                        model=st.session_state["openai_model"],
                        response_format={"type": "json_object"},
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a course textbook problem solution generation machine designed to output in JSON in the format: "
                                + output_example
                                + "\n Follow the format exactly. Must use initial_setup_code to come up with the Correct_code. Ensure the testcases run successfully when concatenated with the Correct_code provided. For any problems whose answer is just a set of import, do not include testcases",
                            },
                            {
                                "role": "user",
                                "content": "Generate the correct code and testcases for the code problem: \n"
                                + problem["Problem_statement"]
                                + "\n using the code setup: \n"
                                + problem["intial_setup_code"],
                            },
                        ],
                        seed=138,
                        temperature=0.1,
                    )
                    correct_code = json.loads(response.choices[0].message.content)
                    problem["Correct_code"] = correct_code["Correct_code"]
                    problem["testcases"] = correct_code["testcases"]
            # print(section_content.choices[0].message.content)
            chapter["sections"][i] = {
                "heading": section,
                "content": section_content.choices[0].message.content,
                "problems": problems["Problems"],
            }
    # print(selected_chapters)
    return selected_chapters


@st.experimental_fragment
def test(i):
    with st.expander("test"):
        if st.button("test", key=i):
            st.write("test")
            st.write(i)


@st.experimental_fragment
def content_selection(selected_chapters, section_selections):

    st.header("Table of Content Selection", divider="violet")
    with st.form(key="content_selection_form"):
        select_all = st.checkbox("Select All")
        for i, chapter in enumerate(st.session_state.chapters):
            section_selections[i] = st.multiselect(
                chapter["chapter_label"], chapter["sections"]
            )
        submitted = st.form_submit_button("Submit")
    if submitted:
        selected_chapters = []
        # st.code(section_selections)
        if select_all:
            selected_chapters = st.session_state.chapters.copy()
        else:
            for i, chapter in enumerate(st.session_state.chapters):
                if section_selections[i] != []:
                    # print(i)
                    selected_chapters.append(chapter.copy())
                    selected_chapters[-1]["sections"] = section_selections[i]
        print(selected_chapters)
        if len(selected_chapters) > 0:
            # replace main area with textbook content
            st.session_state.selected_chapters = generate_content(
                selected_chapters
            ).copy()
            # print(st.session_state.selected_chapters)
        st.switch_page("pages/content_page.py")
        # load_ui(st.session_state.selected_chapters)
    # print(len(st.session_state.selected_chapters))
    # for i, chapter in enumerate(st.session_state.selected_chapters):
    #     test(i)


@st.cache_data
def generate_chapters(topic):
    st.session_state.messages = []
    st.session_state.selected_chapters = []
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
                "content": "You are a course textbook writing expert designed to output in JSON following the format: \n"
                + example,
            },
            {
                "role": "user",
                "content": "Generate the table of contents (include chapter and sections) for a textbook on "
                + topic
                + ".",
            },
        ],
        seed=138,
        temperature=0.1,
    )
    # print(response.choices[0].message.content)
    data = json.loads(response.choices[0].message.content)
    return data["table_of_contents"]["chapters"]


st.header("Topic:", divider="violet")
topic = st.text_area("Enter the topic you want to study")
st.session_state.topic = topic
if st.session_state.topic is not None and st.session_state.topic != "":
    # something()
    # main_area = st.empty()
    st.session_state.chapters = generate_chapters(st.session_state.topic)
    for chapter in st.session_state.chapters:
        chapter["chapter_label"] = (
            str(chapter["chapter_number"]) + ": " + chapter["chapter_title"]
        )

    section_selections = [None] * len(st.session_state.chapters)

    content_selection([], section_selections)
