import gradio as gr
from agent import agent, get_context

# --- Chat state ---
chat_history = []

# --- Chat Function ---
async def chat(user_message, history):
    history = history or []
    history.append({"role": "user", "content": user_message})
    convo = "\n".join(f"{item['role']}: {item['content']}" for item in history)

    context = get_context(user_message)
    full_prompt = f"{convo}\n\nUser query: {user_message}"
    if "No nutritional information found" not in context:
        full_prompt += f"\n\nNutritional Information:\n{context}"

    # Call Gemini LLM using async Agent
    result = await agent.run(full_prompt)

    # Extract plain text from AgentRunResult
    response = result.output if hasattr(result, 'output') else str(result)

    history.append({"role": "assistant", "content": response})
    return history, history, ""

# --- Greeting message ---
async def initial_message():
    greeting = "Hello there!\nI am here to assist you with all of your nutritional needs.\nHow can I help you?"
    history = [{"role": "assistant", "content": greeting}]
    return history, history

# --- Gradio UI ---
with gr.Blocks(title="Nutrition Agent") as demo:
    gr.Markdown("## 🍌🍊 All A-bot Nutrition 🥑🍗🥦")
    
    chatbot = gr.Chatbot(type='messages', label="Nutrition Assitant", elem_id="chatbox")
    msg = gr.Textbox(placeholder="Ask me about nutrition, meals, etc...", label="Your Message")
    clear_btn = gr.Button("Clear Chat")

    state = gr.State([])

    msg.submit(chat, inputs=[msg, state], outputs=[chatbot, state, msg])
    clear_btn.click(lambda: ([], [], ""), None, [chatbot, state, msg])

    demo.load(initial_message, inputs=None, outputs=[chatbot, state])

# --- Launch the app ---
demo.queue().launch()
