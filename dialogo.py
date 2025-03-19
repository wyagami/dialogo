import streamlit as st
import requests
import json
import PyPDF2
from streamlit_chat import message

with st.sidebar:
    st.sidebar.header("Converse com seus Documentos")
    st.sidebar.write("""
    Carregue um PDF ou TXT e interaja com o conteúdo.
    Escolha entre perguntas geradas automaticamente.
                     
    - Ideias? Envie para: 11-990000425 (Willian)
    - Contribua via PIX: wpyagami@gmail.com
    """)

# Função para extrair texto de um PDF
def extract_text_from_pdf(uploaded_file):
    text = ""
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

# Função para interagir com o modelo de IA
def chat_with_llm(user_input, document_text):
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": "Bearer " + st.secrets["qwen_key"],
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": "qwen/qwen2.5-vl-72b-instruct:free",
            "messages": [
                {"role": "system", "content": "Você é um assistente que responde com base no documento fornecido."},
                {"role": "user", "content": f"{document_text}\n\n{user_input}"},
            ],
        })
    )
    
    if response.status_code == 200:
        return response.json().get("choices", [{}])[0].get("message", {}).get("content", "Erro ao obter resposta.")
    else:
        return "Erro ao acessar o modelo de IA."

# Função para gerar 5 perguntas automáticas pela LLM
def generate_auto_questions(document_text):
    questions_prompt = (
        "Com base no documento, gere exatamente 5 perguntas curtas e relevantes que um usuário poderia fazer. "
        "Retorne as perguntas como uma lista de strings com 5 itens, cada um em uma linha separada, "
        "sem numeração, marcadores ou texto adicional. Exemplo de formato esperado:\n"
        "O que o documento diz sobre o tema?\n"
        "Quais são os principais pontos?\n"
        "Qual é a conclusão?\n"
        "Há exemplos práticos mencionados?\n"
        "Como isso impacta a vida cotidiana?"
    )
    questions = chat_with_llm(questions_prompt, document_text)
    try:
        questions_list = [q.strip() for q in questions.strip().split("\n") if q.strip()]
        if len(questions_list) == 5:
            return questions_list
        else:
            return None  # Retorna None se não houver exatamente 5 perguntas
    except:
        return None

# Interface Streamlit
st.title("Chatbot de Documentos")

# Carregar arquivo
uploaded_file = st.file_uploader("Carregue um PDF ou TXT", type=["pdf", "txt"])

if uploaded_file is not None:
    if uploaded_file.type == "application/pdf":
        document_text = extract_text_from_pdf(uploaded_file)
    else:
        document_text = uploaded_file.getvalue().decode("utf-8")

    # Estado da sessão para armazenar mensagens do chat e perguntas
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "auto_questions" not in st.session_state:
        st.session_state.auto_questions = ["Clique em 'Gerar Perguntas' para começar."]

    # Seção de perguntas automáticas
    st.subheader("Perguntas Automáticas")
    if st.button("Gerar Perguntas"):
        with st.spinner("Gerando perguntas..."):
            # Limpar o histórico ao gerar novas perguntas
            st.session_state.messages = []
            auto_questions = generate_auto_questions(document_text)
            if auto_questions is None:
                st.session_state.messages.append({"role": "assistant", "content": "Assistente: Erro ao gerar as 5 perguntas. Tente novamente."})
                st.session_state.auto_questions = ["Erro ao gerar perguntas. Tente novamente."]
            else:
                st.session_state.auto_questions = auto_questions
    
    selected_question = st.selectbox("Escolha uma pergunta:", st.session_state.auto_questions)
    if st.button("Obter Resposta"):
        if selected_question not in ["Clique em 'Gerar Perguntas' para começar.", "Erro ao gerar perguntas. Tente novamente."]:
            # Limpar o histórico antes de adicionar a nova pergunta e resposta
            st.session_state.messages = []
            response = chat_with_llm(selected_question, document_text)
            st.session_state.messages.append({"role": "user", "content": f"Eu: {selected_question}"})
            st.session_state.messages.append({"role": "assistant", "content": f"Assistente: {response}"})

    # Exibir o chat
    if st.session_state.messages:
        st.subheader("Conversa")
        for i, msg in enumerate(st.session_state.messages):
            if msg["role"] == "user":
                message(msg["content"], is_user=True, key=f"user_{i}", avatar_style="🙂")
            else:
                message(msg["content"], is_user=False, key=f"assistant_{i}", avatar_style="🤖")

else:
    st.write("Carregue um arquivo para começar.")