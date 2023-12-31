import os
import re
import urllib.parse
from io import BytesIO
import requests
import time
import argparse
import subprocess
import json
import PyPDF2
import openai
from youtube_transcript_api import YouTubeTranscriptApi
from bs4 import BeautifulSoup
from bs4.element import Comment
from pydub import AudioSegment
import pytube

openai.api_key = os.getenv('OPENAI_API_KEY')
openai_model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo-16k')
if not openai.api_key:
    print('You need to set the OPENAI_API_KEY environment variable.')
    exit(1)



def print_info(message, quiet=False):
    if quiet:
        return
    print(message)

def get_prompt_from_file(filename):
    try:
        with open(filename) as f:
            return f.read()
    except FileNotFoundError:
        return ''

def get_prompt_text(prompt_name, quiet=False):
    prompt = os.getenv(f'{prompt_name.upper()}_PROMPT', get_prompt_from_file(f'{prompt_name.lower()}_prompt.txt'))
    if not prompt:
        print_info(f'{prompt_name.upper()}_PROMPT not set and {prompt_name.lower()}_prompt.txt not found - using default prompt', quiet)
        if prompt_name == 'summary':
            prompt = "Could you summarise this text for me?"
        elif prompt_name == 'sentiment':
            prompt = "Could you tell me the sentiment of this text?"
    return prompt

def get_sentiment(text, sentiment_prompt):
    functions = [
        {
            "name": "get_sentiment_analysis",
            "description": "this function is given an integer sentiment_score from 0 (very bad) to 10 (very good) and a short string sentiment_analysis which describes the result of the analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sentiment_score": {
                        "type": "integer",
                        "description": "The sentiment score from 0 (very bad) to 10 (very good).",
                    },
                    "sentiment_summary": {
                        "type": "string",
                        "description": "A short bit of text describing the sentiment analysis result.",
                    },
                },
                "required": ["sentiment_score", "sentiment_summary"],
            },
        }
    ]
    function_call = {"name": "get_sentiment_analysis"}
    messages = [
        {
            "role": "system",
            "content": "You are a helpful AI assistant who specialises in sentiment analysis. You are given a piece of text and asked to analyse the sentiment."
        },
        {
            "role": "user",
            "content": f"{sentiment_prompt} :: {text}"
        }
    ]
    return get_openai_response(messages, max_retries=5, functions=functions, function_call=function_call)

def get_summary(text, summary_prompt, strict=False):
    messages = [
        {
            "role": "system",
            "content": "You are a helpful AI assistant who specialises in summarising text. You are given a piece of text and asked to summarise it."
        },
        {
            "role": "user",
            "content": f"{summary_prompt} :: {text}"
        }
    ]
    return get_openai_response(messages, max_retries=5, strict=strict)

def get_text_from_youtube_audio(url: str) -> str:
    print_info("Extracting audio and using Whisper to convert to text")
    yt = pytube.YouTube(url)
    t = yt.streams.filter(only_audio=True)
    filename = t[0].download()
    output_filename =  f"output_{os.getpid()}.mp3"
    if os.path.exists(output_filename):
        os.remove(output_filename)
    subprocess.run(["ffmpeg" , "-vn" , "-sn" , "-dn" , "-i" , filename , "-codec:a" , "libmp3lame" , "-qscale:a" , "4" , output_filename])

    audio = AudioSegment.from_mp3(output_filename)

    # PyDub handles time in milliseconds
    ten_minutes = 10 * 60 * 1000

    text = ""
    chunk_filename = f"chunk_{os.getpid()}.mp3"
    for i, chunk in enumerate(audio[::ten_minutes]):
        with open(chunk_filename, "wb") as f:
            chunk.export(f, format="mp3")
        audio_file = open(chunk_filename, "rb")
        text += openai.Audio.transcribe("whisper-1", audio_file)['text']
        audio_file.close()
    if os.path.exists(chunk_filename):
        os.remove(chunk_filename)
    if os.path.exists(output_filename):
        os.remove(output_filename)
    if os.path.exists(filename):
        os.remove(filename)
    return text

def get_text_from_youtube(url: str, fallback_audio=False) -> str:
    video_id = url.split('watch?v=')[-1]
    text = ""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript(['en'])
        text = " ".join([i['text'] for i in transcript.fetch()])
    except:
        print(f"Could not get transcript for {url}")
        if fallback_audio:
            text = get_text_from_youtube_audio(url)
        else:
            exit(1)

    return text

def get_text_from_pdf(url: str) -> str:
    try:
        response = requests.get(url)
        file = BytesIO(response.content)
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Could not get pdf text for {url}")
        print(e)
        exit(1)

def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

def get_text_from_plain_url(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        texts = soup.findAll(string=True)
        visible_texts = filter(tag_visible, texts)
        return u" ".join(t.strip() for t in visible_texts)
    except:
        print(f"Could not get text for {url}")
        exit(1)

def get_text_from_url(url, fallback_audio=False):
    parsed = urllib.parse.urlparse(url)
    if "youtube.com" in parsed.netloc:
        return get_text_from_youtube(url, fallback_audio=fallback_audio)
    elif re.search(r'\.pdf$', parsed.path, re.IGNORECASE):
        return get_text_from_pdf(url)
    else:
        return get_text_from_plain_url(url)


from typing import List, Dict, Optional

def get_openai_response(messages: List[str], max_retries: int = 5, functions: Optional[Dict[str, str]] = None, function_call: Optional[str] = None, strict: bool = False) -> str:
    if strict:
        temperature = 0.1
    else:
        temperature = 1.0
    for i in range(max_retries):
        try:
             # Create a dictionary with the arguments for the create() method
            kwargs = {
                'model': openai_model,
                'messages': messages,
                'temperature': temperature,
            }

            # Add the optional arguments to the dictionary if they are not None
            if functions is not None:
                kwargs['functions'] = functions
            if function_call is not None:
                kwargs['function_call'] = function_call

            # Make the request to the API
            response = openai.ChatCompletion.create(**kwargs)
            if functions is not None:
                return response.choices[0].message['function_call']
            return response.choices[0].message['content']
        except Exception as e:
            if i < max_retries - 1:  # i is zero indexed
                wait_time = (i+1) * 2  # exponential backoff
                print(f"Error: {e}. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise  # re-throw the last exception if all retries fail

def api(url, summary_prompt="", sentiment_prompt="", max_tokens=3000, skip_summary=False, skip_sentiment=False):
    text = get_text_from_url(url)
    if not summary_prompt:
        summary_prompt = get_prompt_text('summary')
    if not sentiment_prompt:
        sentiment_prompt = get_prompt_text('sentiment')
    if not skip_summary:
        summary = get_summary(text, summary_prompt)
    else:
        summary = ""
    if not skip_sentiment:
        sentiment = get_sentiment(text, sentiment_prompt)
    else:
        sentiment = {'sentiment_score': 0, 'sentiment_analisys': 'N/A'}
    return {
        'summary': summary,
        'sentiment_score': sentiment['sentiment_score'],
        'sentiment_analysis': sentiment['sentiment_analisys']
    }

def main():
    parser = argparse.ArgumentParser(description='Process some URL.')
    parser.add_argument('url', type=str, help='The URL to process')
    parser.add_argument('--max_tokens', type=int, default=3000, help='The maximum number of OpenAI tokens in a request')
    parser.add_argument('--quiet', type=bool, default=False, help='Don\'t log anything - just print the response')
    parser.add_argument('--no-summary', action='store_true', help='Do not generate a summary')
    parser.add_argument('--no-sentiment', action='store_true', help='Do not generate a sentiment analysis')
    parser.add_argument('--json', action='store_true', help='Output the result as json (implies --quiet)')
    parser.add_argument('--summary-prompt', type=str, default="", help='Set the summary prompt inline')
    parser.add_argument('--sentiment-prompt', type=str, default="", help='Set the sentiment prompt inline')
    parser.add_argument('--strict', action='store_true', help='Makes the summary more "stright down the line"')
    parser.add_argument('--allow-audio', action='store_true', help='Use the whisper API to transcribe youtube videos with no transcript (requires ffmpeg)')
    args = parser.parse_args()

    url = args.url
    max_tokens = args.max_tokens
    quiet = args.quiet
    json_output = args.json

    if json_output:
        quiet = True

    if not args.summary_prompt:
        summary_prompt = get_prompt_text('summary', quiet)
    else:
        summary_prompt = args.summary_prompt
    if not args.sentiment_prompt:
        sentiment_prompt = get_prompt_text('sentiment', quiet)
    else:
        sentiment_prompt = args.sentiment_prompt

    summary = '';
    result_dict = {
        'summary': '',
        'sentiment_score': 0,
        'sentiment_analysis': 'N/A'
    };

    print_info(f"Getting text from {url}", quiet)
    text = get_text_from_url(url, fallback_audio=args.allow_audio)
    print_info(f"Got {len(text)} characters from {url}", quiet)

    if not args.no_summary:
        print_info(f"Getting summary of {len(text)} characters", quiet)
        summary = get_summary(text, summary_prompt, strict=args.strict)
        result_dict['summary'] = summary
        if not json_output:
            print('Summary:')
            print(result_dict['summary'])

    if not args.no_sentiment:
        print_info(f"Getting sentiment of {len(text)} characters", quiet)
        sentiment = get_sentiment(text, sentiment_prompt)
        sentiment_dict = sentiment.to_dict()
        # Parse the inner JSON structure
        function_result = json.loads(sentiment_dict['arguments'])

        if function_result['sentiment_score']:
            result_dict['sentiment_score'] = function_result['sentiment_score']

        if function_result['sentiment_summary']:
            result_dict['sentiment_analysis'] = function_result['sentiment_summary']

        if not json_output:
            print('Sentiment:')
            print(f"Score: {result_dict['sentiment_score']} || Analysis: {result_dict['sentiment_analysis']}")

    if json_output:
        output = {}
        if not args.no_summary:
            output['summary'] = summary
        if not args.no_sentiment:
            output['sentiment'] = {'score': result_dict['sentiment_score'], 'analysis': result_dict['sentiment_analysis']}
        print(json.dumps(output))

if __name__ == '__main__':
    main()
