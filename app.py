from openai import OpenAI
import streamlit as st
import csv
import recommend

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
MODEL_ROLE = 'assistant'
USER_ROLE = 'user'

ICON_DICT = {
    MODEL_ROLE: '🧞‍♀️',
    USER_ROLE: '💩'
}

st.title("Bound Movie Chatbot 🤖")


def find_movies(prompt):
    # Construct new prompt
    augmented_prompt = f'''The follow text should be a list of movies, which may be spelled incorrectly:

    <MOVIE_LIST>
    {prompt}
    </MOVIE_LIST>

    If it does not seem like a list of movies, respond with the message: "FAILURE"
    
    If it does seem like a list of movies, respond with ONLY the correctly spelled, comma separated list of the movies, and no other text.
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
    ).choices[0].message.content
    
    if response == "FAILURE":
        return
    
    movie_list = [movie.strip() for movie in response.split(',')]

    # Read csv to obtain a list of movie names
    file_path = "movies_metadata.csv"
    movie_names = set()
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            movie_names.add(row["title"])

    result = []
    for movie in movie_list:
        if movie in movie_names:
            result.append(movie)

    return result

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

if "messages" not in st.session_state:
    content = " ".join([
        'Welcome to the Bound Movie Chatbot!! 🎥🎬🍿',
        ' \nPlease list some of your favorite movies, and I will predict other movies you might like.',
        ' \nThe more movies you list, the better the predictions will be! 🧞‍♀️😎'
    ])
    st.session_state.messages = [{"role": MODEL_ROLE, "content": content}]

for message in st.session_state.messages:
    role = message["role"]
    with st.chat_message(role, avatar=ICON_DICT[role]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": USER_ROLE, "content": prompt})
    with st.chat_message(USER_ROLE, avatar=ICON_DICT[USER_ROLE]):
        st.markdown(prompt)

    movie_list = find_movies(prompt)
    print(movie_list)
    message = ""
    if movie_list == None:
        message = "Sorry, I can't help with that! Please provide a list of movies and I will give you some recommendations."
    elif len(movie_list) == 0:
        message = "Sorry, I don't know any of those movies! Please try some others."
    else:
        recommendations = recommend.run_all(movie_list)
        content = [
            f"I was able to find these movies in my dataset: {', '.join(movie_list)}",
            f" \nHere are some other movies you might like: {recommendations}"
        ]
        message = " ".join(content)
        # Model will reply with recommendations based on your preferences (according to K-means model)

    st.session_state.messages.append({"role": MODEL_ROLE, "content": message})
    with st.chat_message(MODEL_ROLE, avatar=ICON_DICT[MODEL_ROLE]):
        st.markdown(message)

# Some movie lists to try!
'''
The Dark,
Trois couleurs : Rouge,
48 Hrs.,
Lost in Translation,
Berlin: Die Sinfonie der Grosstadt,
Live and Let Die,
Cat on a Hot Tin Roof,
Lili Marleen,
Le Mépris,
Das weisse Rauschen,
Terminator 3: Rise of the Machines,
Catwoman,
Crustacés et coquillages,
The Devil Wears Prada,
Romeo + Juliet,
My Own Private Idaho,
Monsoon Wedding,
Reservoir Dogs,
Love Actually,
Notting Hill,
Once Were Warriors,
Je ne suis pas là pour être aimé,
The Poseidon Adventure,
Monsters, Inc.,
The Hours,
The Conversation,
Die Ehe der Maria Brau
'''

'''
Dancer in the Dark,
The Dark,
Miami Vice,
Tron,
The Lord of the Rings,
48 Hrs.,
Edward Scissorhands,
Le Grand Bleu,
Saw,
Le fabuleux destin d'AmÃ©lie Poulain
'''