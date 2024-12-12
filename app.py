from openai import OpenAI
import streamlit as st
import csv

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
MODEL_ROLE = 'assistant'
USER_ROLE = 'user'

ICON_DICT = {
    MODEL_ROLE: '🧞‍♀️',
    USER_ROLE: '💩'
}

st.title("ChatGPT-like clone")


def find_movies(prompt):
    # Read csv to obtain a list of movie names
    file_path = "movies_metadata.csv"
    movie_names = []
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            movie_names.append(row["title"])

    # Construct new prompt
    augmented_prompt = f'''The follow text should be a list of movies, which may be spelled incorrectly:

    <MOVIE_LIST>
    {prompt}
    </MOVIE_LIST>

    If it does not seem like a list of movies, respond with the message: "FAILURE"
    
    If it does seem like a list of movies, respond with a correctly spelled, comma separated list of the movies.
    '''

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that corrects movie titles."
            },
            {
                "role": "user",
                "content": augmented_prompt
            }
        ],
        temperature=0
    )
    return response.choices[0].message.content


if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": MODEL_ROLE, "content": "test"})

for message in st.session_state.messages:
    role = message["role"]
    with st.chat_message(role, avatar=ICON_DICT[role]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": USER_ROLE, "content": prompt})
    with st.chat_message(USER_ROLE, avatar=ICON_DICT[USER_ROLE]):
        st.markdown(prompt)

    with st.chat_message(MODEL_ROLE, avatar=ICON_DICT[MODEL_ROLE]):
        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": MODEL_ROLE, "content": response})