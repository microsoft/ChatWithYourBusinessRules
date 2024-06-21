import streamlit as st

st.set_page_config(page_title="Chat With Your Business Rules", page_icon="📖", layout="wide")

st.image("https://user-images.githubusercontent.com/113465005/226238596-cc76039e-67c2-46b6-b0bb-35d037ae66e1.png")

st.header("Chat With Your Business Rules - Web Frontend")


st.markdown("---")
st.markdown("""
    This engine helps evaluate and explain business rules:
    - Text to Code: Converts business language to the appropraite code.
    - Code to Text: Converts code(s) to business language.
    - Get Product By Expression Search: Returns a product related to a specific business rule expression.

    **👈 Select BotService_Chat from the sidebar** to get started.

    ### Want to learn more?
    - Check out [Github Repo](https://github.com/microsoft/ChatWithYourBusinessRules/)
    - Jump into [Azure OpenAI documentation](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/)

"""
)
st.markdown("---")
