import streamlit as st
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
import re
import os
from dotenv import load_dotenv


load_dotenv()

def sanitize_input(user_input):
    return re.sub(r"[<>'\";]", '', user_input)

def scrape_google(query):
    sanitized_query = sanitize_input(query)
    url = f"https://www.google.com/search?q={sanitized_query}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}"}

        soup = BeautifulSoup(response.text, 'html.parser')
        results = []

        for g in soup.find_all('div', class_='tF2Cxc')[:5]:
            title = g.find('h3').text if g.find('h3') else 'No title available'
            link = g.find('a')['href'] if g.find('a') else 'No link available'
            snippet = g.find('span', class_='aCOpRe').text if g.find('span', class_='aCOpRe') else 'No snippet available'

            results.append({"title": title, "link": link, "snippet": snippet})

        return {"results": results}

    except Exception as e:
        return {"error": str(e)}

def get_ai_answer(query, context):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("API key is missing. Set it in a .env file.")
        
    client = OpenAI(api_key=api_key)

    try:
        context_text = "\n".join(
            [f"Title: {item['title']}\nSnippet: {item['snippet']}\nLink: {item['link']}" for item in context]
        )
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant providing detailed and accurate answers based on the search results. Include specific references to the sources when possible."},
                {"role": "user", "content": f"Given the following context, answer the query: {query}\n\nContext:\n{context_text}"}
            ],
            max_tokens=1000,
            temperature=0.7
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"An error occurred: {e}"

def main():
   
    st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        :root {
            --bg-primary: #0F1117;
            --bg-secondary: #1A1D26;
            --text-primary: #FFFFFF;
            --text-secondary: #8F9BAE;
            --accent-color: #3B82F6;
            --border-radius: 16px;
        }
        * {
            box-sizing: border-box;
            scrollbar-width: thin;
        }
        body {
            font-family: 'Inter', sans-serif !important;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            margin: 0;
            padding: 0;
        }
        .stApp {
            background: var(--bg-primary) !important;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .gradient-header {
            color: var(--text-primary);
            font-size: 2.5rem;
            font-weight: 700;
            text-align: center;
            margin-bottom: 30px;
            background: linear-gradient(90deg, var(--text-primary), var(--accent-color));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -1px;
        }
        .stTextInput > div > input {
            background: var(--bg-secondary) !important;
            border: 1px solid #2D3748 !important;
            color: var(--text-primary) !important;
            border-radius: var(--border-radius) !important;
            padding: 15px 20px !important;
            font-size: 1rem !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        .stTextInput > div > input:focus {
            outline: none !important;
            border-color: var(--accent-color) !important;
            box-shadow: 0 0 0 2px var(--accent-color);
        }
        .stButton > button {
            background: var(--accent-color) !important;
            border: none !important;
            color: white !important;
            border-radius: var(--border-radius) !important;
            padding: 12px 25px !important;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            transform: translateY(-3px);
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
        }
        .stMarkdown {
            background: var(--bg-secondary);
            border-radius: var(--border-radius);
            padding: 20px;
            margin-bottom: 15px;
            border: 1px solid #2D3748;
            color: var(--text-secondary);
        }
        .stMarkdown h3 {
            color: var(--text-primary);
            margin-bottom: 10px;
        }
        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: var(--bg-primary);
        }
        ::-webkit-scrollbar-thumb {
            background: var(--accent-color);
            border-radius: 4px;
        }
        @keyframes fadeIn {
            from { 
                opacity: 0; 
                transform: translateY(20px); 
            }
            to { 
                opacity: 1; 
                transform: translateY(0); 
            }
        }
        .fade-in {
            animation: fadeIn 0.5s ease-out forwards;
        }
    </style>
    """, 
    unsafe_allow_html=True
)
    st.markdown('<div class="gradient-header">AI Answer Engine</div>', unsafe_allow_html=True)
    query = st.text_input("Enter your query or topic:", key="query", placeholder="Ask Question Here...",
                          help="Provide a topic or question to get started")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Get Answer", key="answer_button"):
            if not query:
                st.warning("")
            else:
                st.markdown('<div class="fade-in">✨ Fetching answer...</div>', unsafe_allow_html=True)
                scraped_results = scrape_google(query)
                if "error" in scraped_results:
                    st.error(f"Error: {scraped_results['error']}")
                else:
                    answer = get_ai_answer(query, scraped_results["results"])
                    st.subheader("AI Answer 💡")
                    st.write(answer)
    with col3:
        if st.button("Get Articles", key="articles_button"):
            if not query:
                st.warning("Please enter a query.")
            else:
                st.markdown('<div class="fade-in">📰 Fetching articles...</div>', unsafe_allow_html=True)
                articles = scrape_google(query)
                if "error" in articles:
                    st.error(f"Error: {articles['error']}")
                else:
                    st.subheader("Found Articles 📚")
                    for article in articles["results"]:
                        st.markdown(f"### [{article['title']}]({article['link']})")
                        st.write(article['snippet'])
                        st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; margin-top: 50px;'>
            <p>&copy; All rights reserved, Rishit Seth</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
