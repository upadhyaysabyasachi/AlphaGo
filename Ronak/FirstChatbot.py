import random
import gradio as gr
import os
from groq import Groq

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)




def llm_call(message, history):
    #LLM
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": message,
            }
        ],
        model="llama-3.3-70b-versatile",
    )
    print(chat_completion.choices[0].message.content)
    return(chat_completion.choices[0].message.content)
    
#UI
demo = gr.ChatInterface(llm_call, type="messages", autofocus=False)

if __name__ == "__main__":
    demo.launch()


