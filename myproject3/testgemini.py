import os
from google import genai

api_key = os.environ["GEMINI_API_KEY"]
# print(api_key)

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="models/gemini-flash-latest",
    contents="Say OK"
)

print(response.text)
