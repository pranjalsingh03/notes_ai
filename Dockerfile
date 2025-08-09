FROM python:3.9

RUN apt-get update && apt-get install -y \
    software-properties-common \
    wget \
    git \
    python3 \
    python3-pip \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-xetex \
    latexmk

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

COPY . .


EXPOSE 8000

CMD ["python", "app.py"]
