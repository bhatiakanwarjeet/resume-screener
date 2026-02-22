import os
import time
import streamlit as st
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

MODEL = "llama-3.1-8b-instant"

def generate_text(prompt, temperature=0.4, max_tokens=800):
    try:
        start = time.time()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        latency = round(time.time() - start, 2)
        return response.choices[0].message.content, latency
    except Exception as e:
        st.error(f"LLM API error: {e}")
        return "", 0.0
