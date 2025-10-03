#import libararies
import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()
client = OpenAI()
response = client.responses.create(
    model="gpt-5",
    input="Write a one-sentence bedtime story about a unicorn."
)
print(response.output_text)

#Backend Functions
def echo(message, history):
    return message      

#frontdend
demo = gr.ChatInterface(fn=echo, type="messages", examples=["hello", "hola", "merhaba"], title="Echo Bot")
demo.launch()