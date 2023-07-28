import json
from flask import Flask, request, jsonify
import main

app = Flask(__name__)

@app.route('/api/summarise', methods=['POST'])
def summarise():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    url = data.get('url')
    summary_prompt = data.get('summary_prompt', '')
    sentiment_prompt = data.get('sentiment_prompt', '')
    strict = data.get('strict', False)

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    if not summary_prompt:
        summary_prompt = main.get_prompt_text('summary', quiet=True)

    if not sentiment_prompt:
        sentiment_prompt = main.get_prompt_text('sentiment', quiet=True)

    text = main.get_text_from_url(url, fallback_audio=False)
    summary = main.get_summary(text, summary_prompt, strict=strict)
    sentiment = main.get_sentiment(text, sentiment_prompt)

    sentiment_dict = sentiment.to_dict()
    # Parse the inner JSON structure
    function_result = json.loads(sentiment_dict['arguments'])

    return jsonify({'url': url, 'summary': summary, 'sentiment': {'score': function_result['sentiment_score'], 'summary': function_result['sentiment_summary']}}), 200

if __name__ == '__main__':
    app.run(debug=False)
