from utils import llmCaller as call
from utils import json_parser as jp
import generate_questions as gen
import asyncio
import re
import base64
import os
import generateImage as gi
import insertImage as ins
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type





def encode_image(image_path):
    # Check if the file exists
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"The file {image_path} does not exist.")
    
    # Open the image file in binary mode and read its contents
    with open(image_path, "rb") as image_file:
        # Encode the binary data to base64
        encoded_string = base64.b64encode(image_file.read())
    
    # Convert the bytes to a UTF-8 string
    base64_string = encoded_string.decode('utf-8')
    
    return base64_string



@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
def validate(image_path,code,description):
    image= encode_image(image_path)
    prompt=f"""
    Consider you are an animator and illustrator whose responsibility is to generate an image which can describe the given description.

    You are given with the image and the description carefully analyse the image and tell if the image is in accordance with the description
    provided. In case the image is wrong and is not correct then correct the code given to reconstruct the correct image. In case the image is
    correct do not produce anything.

    The code uses basic shapes in python.

    The description of image is:
    {description}

    Give the output in the following JSON format:
    {{
        "verdict": "correct/wrong whether the code is correct or not which generates the image",
        "code": "if the code is wrong based on the image generated and description provided give the generated code else give the same code as it is."
    }}

    do not print anything else.
    """

    messages= [
            {
                "role": "user",
                "content": [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "text",
                    "text": "The image is: \n"
                },
                {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image}"
                        }
                },
                {
                    "type": "text",
                    "text": f"The code is: \n\n {code}"
                }
                ]
            }
            ] 
    
    response= call.callGPT(messages)

    resp= jp.parse_json_response(response)
    
    return resp




def generate_and_validate(descriptions,codes):
    imgpath= "storageBuffer/code/output_image.png"
    for description,code in zip(descriptions,codes):
        exec(code)
        resp= validate(imgpath,code,description)
        c=0
        while resp['verdict'].lower()=='wrong' or c==3:
            resp= validate(imgpath,code,description)
            c+=1
        
        ncode= resp['code']
        exec(ncode)
        
        

def extract_code(text):
    pattern = r'<code>(.*?)</code>'
    matches = re.findall(pattern, text, re.DOTALL)
    if not matches:
        npattern= r"```python(.*?)```"
        matches= re.findall(npattern,text,re.DOTALL)
    return matches[0]




def get_image_descriptions(text):
    # Regular expression pattern to match text between <img> and </img> tags
    pattern = r'<img>(.*?)</img>'
    
    # Find all matches in the text
    matches = re.findall(pattern, text, re.DOTALL)
    
    return matches


def generate_image_codes(descriptions):

    def extract_code(text):
        pattern = r'<code>(.*?)</code>'
        matches = re.findall(pattern, text, re.DOTALL)
        if not matches:
            npattern= r"```python(.*?)```"
            matches= re.findall(npattern,text,re.DOTALL)
        return matches[0]



    prompt= """
    You are given with the description of a diagram.
    
    Write a code using manim to draw a static image in .png format save the output image as "output_image.png".
    
    Give the code in the following format:
    <code>
    write the code here..
    ....

    </code>

    save the output image to path= "storageBuffer/code/output_image.png"
    
    """
    codes=[]
    for description in descriptions:
        fprompt= prompt+"\n\n"+f"The description of the diagram to be generated is:\n{description}"
        messages= [
            {
                "role": "user",
                "content": [
                {
                    "type": "text",
                    "text": fprompt
                }
                ]
            }
            ]
        resp= call.callGPT(messages)
        code= extract_code(resp)
        codes.append(code)
    

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
def image_validate(imagecode, imagePath, description):
    prompt= f"""
    Consider you are an expert python programmer.

    Here is an image generated by the following code:

    {imagecode}

    The description of the image is:
    {description}

    check if the image given appropriately matches the image description. If it doesn't matches then rewrite a new python code else give the same 
    code.
    make sure that image is saved at {imagePath}.
    """
    
    try:
        image= encode_image(imagePath)
    except:
        return None
    messages= [
            {
                "role": "user",
                "content": [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "text",
                    "text": "The image is: \n"
                },
                {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image}"
                        }
                }
                ]
            }
            ]

    response= call.callGPT(messages)
    code= extract_code(response)
    exec(code)

    return imagePath


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
def validate_code(outputpath):
    with open(outputpath,'r') as f:
        code = f.read()
    
    prompt = f"""
    Check the following latex code if it has any error. Rewrite the new code by correcting the code.
    Give the output in LATEX format.

    the code is:
    {code}

    if the there is no error in the code reprint the same code.
    """
    messages = [
            {
                "role": "user",
                "content": [
                {
                    "type": "text",
                    "text": prompt
                }
                ]
            }
            ]
    
    try:
        response = call.callGPT(messages)
        npattern = r"```latex(.*?)```"
        matches = re.findall(npattern, response, re.DOTALL)
        
        code = matches[0]
        return code
    except Exception as e:
        print(f"Error is : {e}")
        return None
    


def store_to_pdf_path(response, output_path):
    base, filePath = os.path.split(output_path)
    outputpath = ''
    
    print(f'getting pdf...')
    descriptions = get_image_descriptions(response)
    print('========')
    print(f"Length of description: {len(descriptions)}")
    imagelist = []

    for j, desc in enumerate(descriptions):
        basedir,_ = os.path.split(output_path)
        imgpath = os.path.join(basedir,f'outputImage{j+1}.png')
        imagecode = gi.test_code_generation(desc,imgpath)
        
        if imagecode:
            imagepath = image_validate(imagecode,imgpath,desc)
            if imagepath:
                imagelist.append(imagepath)
        
        if not imagecode:
            continue

    inputcodepath = base + f"/{filePath.split('.')[0]}.tex"
    
    outputpath = ins.insert_images_in_latex(inputcodepath, imagelist)
    print(f"fetched response ... stored at {outputpath}")

    code = validate_code(outputpath)
    if not code:
        return outputpath
    print("===NEW CODE GENERATED===")

    output_path = ins.latex_to_pdf(outputpath,output_path)
    if output_path:
        return output_path
    print('Error in converting from latex to pdf')
    return None



@retry(
    stop = stop_after_attempt(3),
    wait = wait_exponential(multiplier=1, min=4, max=10),
    reraise = True
)
def get_AI_notes(cls, subject, chapter, topic, output_path):
    text = gen.get_text(cls, subject, chapter)

    if not text:
        return None
    
    prompt = f"""
    Consider you are a bright student who studies the following text of class {cls} subject {subject}, chapter {chapter} and regarding topic {topic}.

    Analyse the text carefully and make important notes that is elaborative and illustrative out of the given text which will help you in revision
    during exams.

    The text is:
    {text}

    Give your output in the LATEX format:
    
    Heading 
    Topic
    - notes in points.
    ...

    Also if any diagram have to be inserted in the page then give the detailed description of the diagram within the <img> </img> tag.

    Example:

    Light
    Defination

    - Light is an electromagnetic radiation which is produced by the perpendicular intersection of electric and magnetic field at the junction
    of which the wave is produced.

    <img>
        A diagram of the 3d axes in which the x axis is planar on screen showing the direction of electric field, y axis perpendicular to x axis
        but coplanar and showing the direction of magnetic field and z axis perpendicular to the xy plane and showing the direction of light.
    </img>

    ...

    Remember:
    - use proper latex libraries.
    - in case of any notes which requires direction of force properly describe the instrument, direction of force, letters included to represent 
    them etc.
    - give a detailed description as to how the diagram will look visually.
    - the notes must be concise but elaborative enough to include important information think from exam point of view.

    Give a clean and labelled output. Do not worry about length be descriptive.
    """

    messages = [
            {
                "role": "user",
                "content": [
                {
                    "type": "text",
                    "text": prompt
                }
                ]
            }
            ]
    
    max_tokens = 4096
    
    response = ""
    try:
        response = call.callGPT(messages, max_tokens)
        if not response:
            nmsg = f"""
        Consider you are a bright student who studies the following text of class {cls} subject {subject}, chapter {chapter} and regarding topic {topic}.

        Make important notes that is elaborative and illustrative for the given class, subject and chapter above
        which will help you in revision
        during exams.

        Give your output in the LATEX format:
        
        Heading 
        Topic
        - notes in points.
        ...

        Also if any diagram have to be inserted in the page then give the detailed description of the diagram within the <img> </img> tag.

        Example:

        Light
        Defination

        - Light is an electromagnetic radiation which is produced by the perpendicular intersection of electric and magnetic field at the junction
        of which the wave is produced.

        <img>
            A diagram of the 3d axes in which the x axis is planar on screen showing the direction of electric field, y axis perpendicular to x axis
            but coplanar and showing the direction of magnetic field and z axis perpendicular to the xy plane and showing the direction of light.
        </img>

        ...

        Remember:
        - use proper latex libraries
        - in case of any notes which requires direction of force properly describe the instrument, direction of force, letters included to represent 
        them etc.
        - give a detailed description as to how the diagram will look visually.
        - the notes must be concise but elaborative enough to include important information think from exam point of view.

        Give a clean and labelled output. Do not worry about length be descriptive.
        """
            response = call.callGPT(nmsg)
        
        print("response generated....")

        npattern = r"```latex(.*?)```"
        matches = re.findall(npattern, response, re.DOTALL)
        resp = matches[0]
        
        path = store_to_pdf_path(resp, output_path)
        if not path:
            print(f"error is {path}")
            inputcodepath = os.path.split(output_path)[0] + "/input.tex"
            with open(inputcodepath,'w') as f:
                f.write(resp)
            path = ins.latex_to_pdf(inputcodepath, output_path)
        
        return path
    except Exception as e:
        print(f"Error is {e}")  
        return None          


def generateNotes(cls, subject, chapter, topic, output_path):
    text = gen.get_text(cls, subject, chapter)

    text_prompt = f"""
    Consider you are a bright student of class {cls} who is studying subject {subject}, chapter {chapter} and topic {topic}.
    Now you have to make short yet elaborative notes which will help you in revision during exams for the given topic.

    Give your output in following structured format:
    ClassName   SubjectName
    Chapter
    Topic
    - <Begin the notes in points>

    For reference refer the text:
    {text}

    Remember the following points:
    - Be descriptive, elaborative and illustrative in making notes.
    - Include important points, definitions, events which are necessary for exam preparation.
    - Ensure that the notes are formed in points and if paragraphs are there it should be short and concise
    - Make it easily readable and should not be boring.
    - Include any formulae or equation or reaction present in the text which is important.
    - Include list of important questions that can be asked from the topic.
    - Do not include any image.

    #These notes are to be read by students for revision of their examinations so make it easy to read and easily understandable.
    """

    simple_prompt = f"""
    Consider you are a bright student of class {cls} who is studying subject {subject}, chapter {chapter} and topic {topic}.
    Now you have to make short yet elaborative notes which will help you in revision during exams for the given topic.

    Give your output in following structured format:
    ClassName   SubjectName
    Chapter
    Topic
    - <Begin the notes in points>

    Remember the following points:
    - Be descriptive, elaborative and illustrative in making notes.
    - Include important points, definitions, events which are necessary for exam preparation.
    - Ensure that the notes are formed in points and if paragraphs are there it should be short and concise
    - Make it easily readable and should not be boring.
    - Include any formulae or equation or reaction present in the text which is important.
    - Include list of important questions that can be asked from the topic.
    - Do not include any image.

    #These notes are to be read by students for revision of their examinations so make it easy to read and easily understandable.
    """

    if not text:
        prompt = simple_prompt
    else:
        prompt = text_prompt
    
    messages = [
            {
                "role": "user",
                "content": [
                {
                    "type": "text",
                    "text": prompt
                }
                ]
            }
        ]
    
    try:
        response = call.callGPT(messages)
        if not response:
            messages = [
                {
                    "role": "user",
                    "content": [
                    {
                        "type": "text",
                        "text": simple_prompt
                    }
                    ]
                }
            ]
            response = call.callGPT(messages)
        
        latex_code = extract_latex_code(response)
        if not latex_code:
            return None
        ret = ins.convert_latex_to_pdf(latex_code, output_path)
        if not ret:
            return None
        
        return output_path
    except Exception as e:
        print(f"Error occurred: {e}")
        return None
    

def extract_latex_code(response_text):
    prompt = f"""
    You are given with a notes in text format you have to convert it to well structured and labelled LATEX code.
    
    Follow following instructions while converting to LATEX:

    - Properly label the Class, subject, chapter and topic
    - Properly represent any formulae, mathematical functions, equations or chemical reactions
    - Import all necessary latex libraries properly.

    Now convert the following text to LATEX:
    {response_text}
    """

    messages = [
                {
                    "role": "user",
                    "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                    ]
                }
            ]
    
    response = call.callGPT(messages)

    if not response:
        return None
    
    npattern = r"```latex(.*?)```"
    matches = re.findall(npattern, response, re.DOTALL)

    resp = matches[0]
    if not resp:
        return None

    return resp
    
    





