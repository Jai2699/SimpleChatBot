import openai
import PyPDF2
import streamlit as st
import io

# Set up OpenAI API key
openai.api_key ="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"
# Store chat history and settings
if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'pdf_texts' not in st.session_state:
    st.session_state['pdf_texts'] = []
if 'conversation' not in st.session_state:
    st.session_state['conversation'] = []

# Function to extract text from PDFs along with page numbers and file names
def extract_text_from_pdfs(pdf_files):
    pdf_texts = []
    for pdf_file in pdf_files:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        pdf_file_name = pdf_file.name  # Get the PDF file name for reference
        for page_number in range(len(pdf_reader.pages)):
            page_text = pdf_reader.pages[page_number].extract_text()
            pdf_texts.append({
                'text': page_text,
                'pdf_file': pdf_file_name,
                'page_number': page_number + 1  # Page numbers start from 1
            })
    return pdf_texts

# Function to ask ChatGPT a question based on the extracted PDF content
def ask_chatgpt(extracted_texts, question, temperature, max_tokens):
    combined_text = ""
    pdf_references = []
    
    # Combine text from different PDFs and create references for each
    for text_info in extracted_texts:
        combined_text += text_info['text'] + "\n"
        pdf_references.append(f"From {text_info['pdf_file']} (Page {text_info['page_number']}): {text_info['text'][:200]}...")

    # Create conversation history context if any
    if st.session_state['conversation']:
        conversation_context = "\n".join([f"Q: {msg['question']}\nA: {msg['answer']}" for msg in st.session_state['conversation']])
    else:
        conversation_context = ""

    # Send the extracted content and question to the ChatGPT model
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"I have the following content from multiple PDFs:\n\n{'\n\n'.join(pdf_references)}\n\n{conversation_context}\nQ: {question}\nA:"}
    ]
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature
    )
    
    answer = response['choices'][0]['message']['content'].strip()

    # Find the PDF source of the answer
    answer_source = None
    for text_info in extracted_texts:
        if text_info['text'][:200] in answer:
            answer_source = f"From {text_info['pdf_file']} (Page {text_info['page_number']})"
            break

    if not answer_source:
        answer_source = "Source PDF not identified."

    return answer, answer_source

# Function to summarize the uploaded PDF content
def summarize_pdf_content(extracted_texts):
    combined_text = " ".join([text_info['text'] for text_info in extracted_texts])

    # Prompt to summarize the content
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"Please summarize the following text:\n\n{combined_text}"}
    ]
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=300,
        temperature=0.5
    )
    
    summary = response['choices'][0]['message']['content'].strip()
    return summary

# Set up background image using CSS
st.markdown(
    """
    <style>
    .title {
        color: #4CAF50;
        text-align: center;
        font-size: 3em;
    }
    .info {
        background-color: #f9f9f9;
        padding: 10px;
        border-radius: 5px;
        margin-top: 20px;
    }
    .answer {
        background-color: #ffffff;
        color: #000000;
        padding: 10px;
        border-radius: 5px;
        margin-top: 20px;
        font-family: 'Courier New', Courier, monospace;
        font-size: 1.2em;
        border: 2px solid #ccc;
    }
    .reference {
        color: #007bff;
        font-size: 1em;
    }
    /* Add the background image */
    body {
        background-image: url('https://your-image-url.com/image.jpg');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    </style>
    """, unsafe_allow_html=True
)

# App title with color
st.markdown('<h1 class="title">PDF-based Chatbot</h1>', unsafe_allow_html=True)

# Sidebar for useful links, history, and additional info
st.sidebar.title("App Sidebar")
st.sidebar.subheader("Navigation")

# Links for further references (e.g., OpenAI docs, Streamlit docs)
st.sidebar.markdown("""
### Useful References:
- [OpenAI Documentation](https://platform.openai.com/docs/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [PyPDF2 Documentation](https://pypdf2.readthedocs.io/en/latest/)
""")

# File uploader for PDFs
uploaded_files = st.sidebar.file_uploader("Upload PDF files", accept_multiple_files=True, type=['pdf'])

# Sidebar settings for ChatGPT
st.sidebar.subheader("ChatGPT Settings")
temperature = st.sidebar.slider("Temperature (Creativity Level)", 0.0, 1.0, 0.7)
max_tokens = st.sidebar.slider("Max Tokens (Response Length)", 100, 500, 300)

# Button to clear chat history
if st.sidebar.button("Clear Chat History"):
    st.session_state['history'] = []
    st.session_state['conversation'] = []

# PDF upload and extraction
if uploaded_files:
    extracted_texts = extract_text_from_pdfs(uploaded_files)
    st.session_state['pdf_texts'] = extracted_texts
    st.success("PDF content extracted successfully!")

# Button to summarize PDF content
if st.sidebar.button("Summarize PDF"):
    if st.session_state['pdf_texts']:
        summary = summarize_pdf_content(st.session_state['pdf_texts'])
        st.markdown(f"<div class='info'><b>Summary:</b> {summary}</div>", unsafe_allow_html=True)
    else:
        st.warning("Please upload PDFs first.")

# Text input for asking questions
question = st.text_input("Ask a question based on the PDF content:")

# Button to get an answer from ChatGPT
if st.button("Get Answer"):
    if question and st.session_state['pdf_texts']:
        answer, source_info = ask_chatgpt(st.session_state['pdf_texts'], question, temperature, max_tokens)
        st.markdown(f"<div class='answer'><b>Answer:</b> {answer}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='reference'><b>Source:</b> {source_info}</div>", unsafe_allow_html=True)
        
        # Store the conversation in session state for multi-turn dialogue
        st.session_state['conversation'].append({'question': question, 'answer': answer})
        
        # Store the question, answer, and source information in session state for history
        st.session_state['history'].append({'question': question, 'answer': answer, 'source': source_info})
    else:
        st.warning("Please upload PDFs and ask a question.")

# Sidebar history
if st.session_state['history']:
    st.sidebar.subheader("Previous Questions")
    for i, item in enumerate(st.session_state['history'], 1):
        st.sidebar.write(f"Q{i}: {item['question']}")
        st.sidebar.write(f"A{i}: {item['answer']}")

# Button to download chat history
if st.sidebar.button("Download Chat History"):
    if st.session_state['history']:
        chat_history = "\n".join([f"Q: {item['question']}\nA: {item['answer']}\n" for item in st.session_state['history']])
        st.download_button(label="Download Chat History", data=chat_history, file_name="chat_history.txt")
    else:
        st.warning("No chat history available.")
