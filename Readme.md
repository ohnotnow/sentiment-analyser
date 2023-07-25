# Text Analysis CLI Tool

This is a Python command-line tool that takes a URL as input and uses the OpenAI API to generate a summary and sentiment analysis of the text found at the URL. It can process plain text from HTML pages, transcripts from YouTube video links, and text from PDF documents.

## Installation

Clone this repository to your local machine:

```bash
git clone https://github.com/ohnotnow/sentiment-analyser
```

Navigate to the repository directory:

```bash
cd sentiment-analyser
```

Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Configuration

The tool uses several environment variables for configuration:

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `OPENAI_MODEL`: The OpenAI model to use (default: 'gpt-3.5-turbo-16k')
- `SUMMARY_PROMPT`: The prompt for the summary request (default: 'Could you summarise this text for me?')
- `SENTIMENT_PROMPT`: The prompt for the sentiment request (default: 'Could you tell me the sentiment of this text?')

You can set these environment variables in your shell, or you can create a text file with the prompt in the same directory as the script. For example, for `SUMMARY_PROMPT`, you can create a file named `summary_prompt.txt`.

If a prompt is not set via an environment variable or a text file, the default prompt will be used.

## Usage

Run the tool with the following command:

```bash
python main.py <url>
```

Replace `<url>` with the URL to process.

The tool also accepts the following optional command-line flags:

- `--max_tokens=<number>`: The maximum number of OpenAI tokens in a request (default: 3000)
- `--quiet`: If set, the tool will not log anything, it will just print the response
- `--no-summary`: If passed, the tool will not perform a summary of the text
- `--no-analysis`: If passed, the tool will not perform sentiment analysis
- `--json`: If passed, the tool outputs the results as a json string
- `--summary-prompt`: Set the summary prompt inline (eg, `--summary-prompt="Could you summarise this in bullet points?"`)
- `--sentiment-prompt`: Set the sentiment prompt inline
- `--strict`: Set the summary to be more 'straight down the line' and less 'creative'

For example, to process a URL with a maximum of 2000 tokens and without logging, you would run:

```bash
python main.py --max_tokens=2000 --quiet https://www.example.com
```

See also the example `batch.sh` for an example of using the command to process a long list of URL's.
## Output

The tool will print the summary and sentiment analysis of the text found at the URL. The sentiment analysis includes a score from 0 (very bad) to 10 (very good) and a short summary of the sentiment.  Example from a review of an Air Fryer :

> Summary: The COSORI Lite air fryer is a compact and affordable option for those looking for an air fryer. It has a sleek design and offers advanced features such as preheat and keep warm functions. It performed well in cooking tests, producing golden and fluffy chips, quick and hot frozen bites, crispy air-fried broccoli, and evenly cooked bacon. The air fryer is easy to use with its touch screen panel and LED screen. It also comes with helpful presets for chicken, fries, bacon, steak, and veggies. The COSORI Lite air fryer is recommended for small households of two to three people. It is energy-efficient and comes with a recipe booklet and access to the COSORI app for more ideas. Overall, it is a good buy for its price and performance.
>
> Sentiment:
> Score: 8 || Analysis: Positive
