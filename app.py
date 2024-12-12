import time
import os
import joblib
import streamlit as st
import openai
import csv

# Set your OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"]

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

    response = openai.ChatCompletion.create(
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


new_chat_id = f'{time.time()}'
MODEL_ROLE = 'assistant'
AI_AVATAR_ICON = '🧞‍♀️'

# Create a data/ folder if it doesn't already exist
try:
    os.mkdir('data/')
except:
    # data/ folder already exists
    pass

# Load past chats (if available)
try:
    past_chats: dict = joblib.load('data/past_chats_list')
except:
    past_chats = {}

# Sidebar allows a list of past chats
with st.sidebar:
    st.write('# Past Chats')
    if st.session_state.get('chat_id') is None:
        st.session_state.chat_id = st.selectbox(
            label='Pick a past chat',
            options=[new_chat_id] + list(past_chats.keys()),
            format_func=lambda x: past_chats.get(x, 'New Chat'),
            placeholder='_',
        )
    else:
        st.session_state.chat_id = st.selectbox(
            label='Pick a past chat',
            options=[new_chat_id, st.session_state.chat_id] + list(past_chats.keys()),
            index=1,
            format_func=lambda x: past_chats.get(x, 'New Chat' if x != st.session_state.chat_id else st.session_state.chat_title),
            placeholder='_',
        )
    st.session_state.chat_title = f'ChatSession-{st.session_state.chat_id}'


st.write('# Bound Movie Chatbot 🤖')

# Chat history (allows multiple questions)
try:
    st.session_state.messages = joblib.load(
        f'data/{st.session_state.chat_id}-st_messages'
    )
    print('old cache')
except:
    st.session_state.messages = []
    print('new_cache made')

# Display a greeting if it's a new chat
if len(st.session_state.messages) == 0:
    with st.chat_message(MODEL_ROLE, avatar=AI_AVATAR_ICON):
        message_placeholder = st.empty()
        message = [
            'Welcome to the Bound Movie Chatbot!! 🎥🎬🍿',
            ' \nPlease list some of your favorite movies, and I will predict other movies you might like.',
            ' \nThe more movies you list, the better the predictions will be! 🧞‍♀️😎'
        ]
        message_placeholder.markdown(" ".join(message))

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(
        name=message['role'],
        avatar=message.get('avatar', None),
    ):
        st.markdown(message['content'])

# React to user input
if prompt := st.chat_input('Your message here...'):
    # Save this as a chat for later
    if st.session_state.chat_id not in past_chats.keys():
        past_chats[st.session_state.chat_id] = st.session_state.chat_title
        joblib.dump(past_chats, 'data/past_chats_list')

    # Display user message in chat message container
    with st.chat_message('user'):
        st.markdown(prompt)

    # Add user message to chat history
    st.session_state.messages.append(
        dict(
            role='user',
            content=prompt,
        )
    )

    # Process user input
    movies_list = find_movies(prompt)
    print(movies_list)

    # Call OpenAI with the entire message history
    # We assume the system message sets the tone/context of the assistant
    # If you need a system prompt, you can prepend it to st.session_state.messages
    full_prompt = st.session_state.messages

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=full_prompt,
        stream=True,
        temperature=0.7
    )

    # Display assistant response in chat message container
    with st.chat_message(
        name=MODEL_ROLE,
        avatar=AI_AVATAR_ICON,
    ):
        message_placeholder = st.empty()
        full_response = ''
        # Stream the response
        for chunk in response:
            delta = chunk.choices[0].delta.get("content", "")
            full_response += delta
            # Rewrites with a cursor at the end
            message_placeholder.write(full_response + '▌')
            time.sleep(0.05)
        # Write the full message after streaming completes
        message_placeholder.write(full_response)

    # Add assistant response to chat history
    st.session_state.messages.append(
        dict(
            role=MODEL_ROLE,
            content=full_response,
            avatar=AI_AVATAR_ICON,
        )
    )

    # Save to file
    joblib.dump(
        st.session_state.messages,
        f'data/{st.session_state.chat_id}-st_messages',
    )
