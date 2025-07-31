import gradio as gr
from agent import agent, get_context
# from pydantic_ai import Agent
# from pydantic_ai.models.google import GoogleModel
# from pydantic_ai.providers.google import GoogleProvider

# --- Hardcoded API Key (Use env vars for production!) ---
# GOOGLE_API_KEY = 'AIzaSyB8N6cic96yyVx3UAlLt6tvZQTYAjNNlWc'

# --- Set up Gemini Agent ---
# provider = GoogleProvider(api_key=GOOGLE_API_KEY)
# model = GoogleModel('gemini-2.5-flash',provider=provider)   
# agent = Agent(model=model)

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


# --- Gradio UI ---
with gr.Blocks(title="Nutrition Agent") as demo:
    gr.Markdown("## 🍌🍊 All A-bot Nutrition 🥑🍗🥦")
    
    chatbot = gr.Chatbot(type='messages', label="Nutrition Assitant")
    msg = gr.Textbox(placeholder="Ask me about nutrition, meals, etc...", label="Your Message")
    clear_btn = gr.Button("Clear Chat")

    state = gr.State([])

    msg.submit(chat, inputs=[msg, state], outputs=[chatbot, state, msg])
    clear_btn.click(lambda: ([], [], ""), None, [chatbot, state, msg])

# --- Launch the app ---
demo.queue().launch()
 