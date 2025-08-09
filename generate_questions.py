from pymongo.mongo_client import MongoClient
from dotenv import load_dotenv
import os
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
load_dotenv()

uri = os.getenv('CONNECTION_STRING')
# Create a new client and connect to the server
client = MongoClient(uri)




def get_text(cls,subject,chapter):
    cluster= client['textbookDB']
    col= cluster['TextbookCollection']

    text=""
    try:
        result = col.find_one({}, {f'{cls}': 1})
        print("text fetched....")
        # print(result)

        # Access the value
        if result and cls in result and subject in result[cls] and chapter in result[cls][subject]:
            text = result[cls][subject][chapter]
            # print(f"The value is: {text}")
            with open('tempText.txt','w') as f:
                f.write(text)
        else:
            print("No matching document found or the specified path doesn't exist")
    except Exception as e:
        print(e)
        return None
    return text
