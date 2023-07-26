from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/summarise', methods=['POST'])
def summarise():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    url = data.get('url')
    summary_prompt = data.get('summary_prompt')

    if not url or not summary_prompt:
        return jsonify({'error': 'Missing url or summary_prompt'}), 400

    # Here is where you would perform your summarization operation.
    # I'm just returning the input for demonstration purposes.

    return jsonify({'url': url, 'summary_prompt': summary_prompt}), 200

if __name__ == '__main__':
    app.run(debug=True)
