from ollama import chat

response = chat(
    model="gemma3:1b",  
    messages=[
        {
            "role": "user",
            "content": "سلام، فقط بگو تست موفق بود."
        }
    ]
)

print(response.message.content)