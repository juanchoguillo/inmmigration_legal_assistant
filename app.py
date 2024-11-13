import streamlit as st
from langchain_groq import ChatGroq
from langchain_community.utilities import ArxivAPIWrapper, WikipediaAPIWrapper
from langchain_community.tools import ArxivQueryRun, WikipediaQueryRun, DuckDuckGoSearchRun
from langchain.agents import initialize_agent, AgentType
from langchain.callbacks import StreamlitCallbackHandler
import smtplib
from email.mime.text import MIMEText
import os 
from dotenv import load_dotenv
import time
import random

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# Custom CSS for responsiveness
st.markdown("""
    <style>
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        /* Responsive design for different screen sizes */
        @media (max-width: 768px) {
            .stApp {
                padding: 1rem;
            }
            .stTextInput > div > div > input {
                font-size: 14px;
            }
            .stMarkdown {
                font-size: 14px;
            }
        }
        
        /* Loading animation styles */
        .loading-container {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(255, 255, 255, 0.8);
            z-index: 9999;
        }
        
        .loading-spinner {
            width: 50px;
            height: 50px;
            border: 5px solid #f3f3f3;
            border-top: 5px solid #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
""", unsafe_allow_html=True)

ASSOCIATED_ATTORNEYS = [
    {
        "name": "Maria Rodriguez",
        "specialty": "Inmigración Familiar",
        "website": "https://bizbridge.ai/maria-rodriguez",
    },
    {
        "name": "Carlos Hernandez",
        "specialty": "Asilo y Refugio",
        "website": "https://bizbridge.ai/carlos-hernandez",
    },
    {
        "name": "Ana Martinez",
        "specialty": "Visas de Trabajo",
        "website": "https://bizbridge.ai/ana-martinez",
    }
]

def translate_to_spanish(text):
    """
    Translates the given text to Spanish using the Groq model
    """
    translator = ChatGroq(
        groq_api_key=api_key,
        model_name="gemma2-9b-it",
        streaming=False
    )
    
    translation_prompt = f"""Translate the following text to Spanish. Maintain any links or special formatting in the text. 
    Only return the translation, nothing else.
    
    Text to translate: {text}"""
    
    response = translator.invoke(translation_prompt)
    return response.content

def get_attorney_recommendation(attorney):
    return f"\n\nPara obtener asesoría legal profesional, te recomiendo contactar a {attorney['name']}, especialista en {attorney['specialty']}. Puedes encontrar más información en: [{attorney['name']}]({attorney['website']})"

def show_loading_screen():
    st.markdown("""
        <div class="loading-container">
            <div class="loading-spinner"></div>
        </div>
    """, unsafe_allow_html=True)

def send_user_info(name, phone_number, user_state):
    msg = MIMEText(f"Name: {name}\nPhone Number: {phone_number}\nState: {user_state}")
    msg['Subject'] = f"{name}, {phone_number}, {user_state}"
    msg['From'] = "juancardona0607@gmail.com"
    msg['To'] = "juan@bizbridge.ai"

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login("juancardona0607@gmail.com", os.getenv("APP_PASSWORD"))
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Error sending email: {e}")
        return False

def initialize_chat_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "¡Hola! Soy un asistente de inmigración. ¿Cómo puedo ayudarte hoy con cualquier pregunta o inquietud relacionada con la ley y los procesos de inmigración?"
            }
        ]
    if "assigned_attorney" not in st.session_state:
        st.session_state.assigned_attorney = random.choice(ASSOCIATED_ATTORNEYS)  # Assign random attorney by default

def validate_phone_number(phone_input):
    return ''.join(filter(str.isdigit, phone_input))

def main():
    st.title("Asistente de Inteligencia Artificial para Inmigración")
    
    """
    Esta inteligencia artificial (AI) fue creada por `Biz Bridge AI` hecha para ayudar a nuestra comunidad 
    y despejar ciertas dudas con respecto a temas legales migratorios en Estados Unidos. 
    No es un asesor legal y recomendamos siempre asesorarse con un abogado. 
    [Biz Bridge AI LLC](https://bizbridge.ai) es una empresa que desarrolla aplicaciones
    de inteligencia artififial para mejorar las ganancias de pequeñas y medianas empresas
    """

    if "user_info_submitted" not in st.session_state:
        st.session_state.user_info_submitted = False
    
    if "loading" not in st.session_state:
        st.session_state.loading = False

    if not st.session_state.user_info_submitted:
        st.subheader("Información del Usuario")
        
        name = st.text_input("Ingresa tu nombre:")
        
        # Phone number input with number validation
        phone_input = st.text_input("Ingresa tu teléfono:", 
                                  help="Solo números permitidos")
        phone_number = validate_phone_number(phone_input)
        if phone_input != phone_number:
            st.warning("Por favor, ingresa solo números en el campo de teléfono.")
        
        states = ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 
                 'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 
                 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 
                 'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota', 
                 'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 
                 'New Hampshire', 'New Jersey', 'New Mexico', 'New York', 
                 'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 
                 'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota', 
                 'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington', 
                 'West Virginia', 'Wisconsin', 'Wyoming']
        user_state = st.selectbox("Selecciona el estado donde vives:", states)
        
        if st.button("Enviar"):
            if name and phone_number and user_state:
                if send_user_info(name, phone_number, user_state):
                    st.session_state.loading = True
                    show_loading_screen()
                    time.sleep(0.3)  # Add a small delay to show the loading animation
                    st.session_state.user_info_submitted = True
                    st.rerun()
            else:
                st.warning("Por favor completa todos los campos.")

    else:
        initialize_chat_state()
        
        arxiv_wrapper = ArxivAPIWrapper(top_k_results=1, doc_content_chars_max=1000)
        arxiv = ArxivQueryRun(api_wrapper=arxiv_wrapper)
        
        wiki_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=1000)
        wiki = WikipediaQueryRun(api_wrapper=wiki_wrapper)
        
        search = DuckDuckGoSearchRun(name="Search")
        
        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg['content'])

        if prompt := st.chat_input(placeholder="¿Cómo puedo ayudarte?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            llm = ChatGroq(
                groq_api_key=api_key, 
                model_name="gemma2-9b-it", 
                streaming=True
            )
            tools = [wiki, arxiv, search]

            prompt_for_search_agent = """You are an immigration assistant AI, designed to help users with questions and concerns related to immigration law and processes in the United States. Your goal is to provide helpful information to the user, and if necessary, suggest consulting with a specialized immigration attorney.

            When the user asks you a question, you should first try to provide a relevant and informative response based on your knowledge. If you are unable to fully address the user's question, you should then search the web (using the provided search tools) to find the most up-to-date and accurate information to share with the user.

            After providing the user with your response, you should always recommend that they consult with a specialized immigration attorney for any complex or sensitive matters. Your role is to assist the user, not to provide legal advice.

            Remember to be respectful, empathetic, and to tailor your language and tone to the user's needs."""

            search_agent = initialize_agent(
                tools=tools,
                llm=llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                handling_parsing_errors=True,
                prompt=prompt_for_search_agent,
            )
            
            with st.chat_message("assistant"):
                st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False)
                
                # Get the agent's response
                response = search_agent.run(st.session_state.messages, callbacks=[st_cb])
                
                # Translate the response to Spanish
                translated_response = translate_to_spanish(response)
                
                # Add attorney recommendation using the assigned attorney
                full_response = translated_response + get_attorney_recommendation(st.session_state.assigned_attorney)
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.write(full_response)

if __name__ == "__main__":
    main()