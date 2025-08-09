from utils import llmCaller as call
from utils import json_parser as jp
import re
import traceback

def test_code_generation(task,imgpath,userprompt=None):
    def extract_code(text):
        npattern= r"```python(.*?)```"
        try:
            matches= re.findall(npattern,text,re.DOTALL)
        except:
            return None
        
        return matches[0]

    prompt= f"""
    You are given with the description of a diagram.
    
    Write a code using in python to draw a static image in .png format.
    
    Give the code in python using PIL and Image libraries only.
    You have to make to a diagram using simple shapes.
    In case the description of the diagram is too complex to draw it using simple shapes then print 'no code'
    
    write the python code using basic shapes only.

    save the output image to path= {imgpath}

    do not print anything else.
    """

    if userprompt:
        userprompt= userprompt
    
    else:
        userprompt= f"""
        The description of image is:
        {task}
        """

    messages= [
            {
                "role": "system",
                "content": [
                {
                    "type": "text",
                    "text": prompt
                }
                ]
            },
            {
                "role": "user",
                "content": [
                {
                    "type": "text",
                    "text": userprompt
                }
                ]
            }
            ] 
    
    response= call.callGPT(messages)
    with open("temp.txt","w") as f:
        f.write(response)

    code= extract_code(response)
    return code


def execute_code(desc,imgpath):
    code= test_code_generation(desc,imgpath)
    try:
        exec(code)
    except Exception as e:
        print(e)
        print('====')
        # message= traceback.print_exc(e)
        message= e
        print(message)
        c=0
        while True:
            userprompt= f"""
            The following code the error rewrite the code after correcting it.

            The code is:
            {code}

            The error is:
            {message}

            The description of the image is:
            {desc}
            """
            ncode= test_code_generation(desc,imgpath,userprompt)
            try:
                print(f"trial {c+1}....")
                exec(ncode)
                break
            except Exception as ee:
                print(ee)
                message= ee
                c+=1
                pass

    print("executed...")
    print(imgpath)
    return code,imgpath


# desc= """
# there is plank inclined at 30 degree angle from horizontal and a box is kept on the inclined slope of the plank.
# """

# execute_code(desc)
