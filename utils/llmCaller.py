
from openai import AzureOpenAI

import os
from dotenv import load_dotenv
import asyncio
import tiktoken

load_dotenv()

api_key= os.getenv("GPT4V_KEY")
endpoint= os.getenv("GPT4V_ENDPOINT")

version = os.getenv('API_VERSION')


client = AzureOpenAI(azure_endpoint=endpoint,api_key=api_key,api_version=version)

def checkTokenLength(messages):
    text = str(messages)
    tokenizer = tiktoken.get_encoding("cl100k_base")  # Default tokenizer for most OpenAI models
    tokens = tokenizer.encode(text)
    
    if len(tokens) > 127999:
        return False
    return True

def callGPT(messages, max_tokens = 4096):
    ret = checkTokenLength(messages)
    print(ret)
    if not ret:
        return False
    
    output = client.chat.completions.create(
        model = "gpt4onew",
        messages = messages,
        max_tokens = max_tokens
        
      )
    response = output.choices[0].message.content
    return response


async def stream_azure_openai(messages,max_tokens=4096):
    # Send a streaming request to Azure OpenAI
    stream = await client.chat.completions.create(
        model="gpt-4onew", # replace with your deployed model name
        messages=messages,
        stream=True,
        max_tokens=max_tokens
    )

    # Process the streaming response
    async for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            resp= chunk.choices[0].delta.content
            # print(chunk.choices[0].delta.content, end='', flush=True)
            yield resp


async def stream_caller(messages,max_tokens=4096):
    response= ""
    flag=0
    try:
      async for content in stream_azure_openai(messages,max_tokens):
        response+= content
    except:
       flag=1
       return response,flag

    return response,flag