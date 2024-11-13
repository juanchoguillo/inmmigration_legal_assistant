import streamlit as st
from langchain_groq import ChatGroq
from langchain_community.utilities import ArxivAPIWrapper, WikipediaAPIWrapper
from langchain_community.tools import ArxivQueryRun, WikipediaQueryRun, DuckDuckGoSearchRun
from langchain.agents import initialize_agent, AgentType
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler  # Updated import
import smtplib
from email.mime.text import MIMEText
import os 
from dotenv import load_dotenv
import time
import random

# ... (previous code remains the same until the main function)

def main():
    # ... (previous code remains the same until the agent initialization)

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

        When responding, always follow this format:
        Thought: Think about what information or resources would be most helpful
        Action: Choose one of the available tools (Search, Wikipedia, or Arxiv)
        Action Input: The specific query to search for
        Observation: Review the search results
        Thought: Analyze if the information is sufficient or if more searching is needed
        Final Answer: Provide the complete response to the user

        Remember to:
        1. Be clear and concise
        2. Use simple language
        3. Always provide actionable information
        4. Suggest consulting with an attorney for complex matters
        """

        search_agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            handle_parsing_errors=True,  # Changed from handling_parsing_errors to handle_parsing_errors
            verbose=True,
            agent_kwargs={
                "format_instructions": prompt_for_search_agent
            }
        )
        
        with st.chat_message("assistant"):
            st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False)
            
            try:
                # Get the agent's response with error handling
                response = search_agent.invoke(
                    {"input": prompt},
                    callbacks=[st_cb]
                )
                
                # Extract the actual response text
                response_text = response.get('output', "Lo siento, no pude procesar tu pregunta. Por favor, intenta reformularla.")
                
                # Translate the response to Spanish
                translated_response = translate_to_spanish(response_text)
                
                # Add attorney recommendation using the assigned attorney
                full_response = translated_response + get_attorney_recommendation(st.session_state.assigned_attorney)
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.write(full_response)
            except Exception as e:
                error_message = translate_to_spanish(f"Lo siento, hubo un error al procesar tu pregunta. Por favor, intenta reformularla de otra manera.")
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})

if __name__ == "__main__":
    main()
