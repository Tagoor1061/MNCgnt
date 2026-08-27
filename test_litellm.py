import os
import litellm

response = litellm.completion(
    model="gpt-4.1-mini",   # use a supported model
    api_key=os.getenv("VERCEL_AI_GATEWAY_API_KEY"),
    messages=[{"role":"user","content":"Hello AI!"}]
)
print(response)
