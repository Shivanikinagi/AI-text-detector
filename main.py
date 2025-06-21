import os
import secrets
import torch
from flask import Flask, render_template, request, jsonify
from transformers import BertForSequenceClassification, BertTokenizer
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB file size limit
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'txt'}
app.config['MODEL_PATH'] = "bert-base-uncased"
app.config['OUTPUT_FILE'] = 'ai_paragraphs.txt'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# Helper function
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# Load model and tokenizer
try:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load with caching
    model = BertForSequenceClassification.from_pretrained(
        app.config['MODEL_PATH'],
        cache_dir='./model_cache'
    )
    tokenizer = BertTokenizer.from_pretrained(
        app.config['MODEL_PATH'],
        cache_dir='./model_cache'
    )

    # Parallelize if multiple GPUs available
    if torch.cuda.device_count() > 1:
        model = torch.nn.DataParallel(model)

    model.to(device)
    model.eval()

except Exception as e:
    raise RuntimeError(f"Model loading failed: {str(e)}")


@app.route('/', methods=['GET'])
def home():
    """Render the main page"""
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    """Handle file upload and analysis"""
    # Check if file exists in request
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    # Validate file
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only .txt files allowed"}), 400

    try:
        # Secure file handling
        filename = secure_filename(f"{secrets.token_hex(8)}.txt")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Read and process file
        with open(filepath, 'r', encoding='utf-8') as f:
            test_essays = [line.strip() for line in f if line.strip()]

        if not test_essays:
            return jsonify({"error": "File is empty"}), 400

        # Process in batches
        batch_size = 32
        results = []
        ai_paragraphs = []

        for i in range(0, len(test_essays), batch_size):
            batch = test_essays[i:i + batch_size]

            # Tokenize batch
            inputs = tokenizer(
                batch,
                padding=True,
                truncation=True,
                return_tensors='pt'
            ).to(device)

            # Predict
            with torch.no_grad():
                outputs = model(**inputs)
                logits = outputs.logits

            # Process predictions
            if logits.size(1) == 1:  # Binary
                probs = torch.sigmoid(logits).squeeze().cpu().numpy()
                preds = (probs > 0.5).astype(int)
            else:  # Multi-class
                probs = torch.softmax(logits, dim=1).cpu().numpy()
                preds = probs.argmax(axis=1)

            # Format results
            for j, (essay, pred, prob) in enumerate(zip(batch, preds, probs)):
                result = {
                    "id": i + j + 1,
                    "text": essay,
                    "is_ai": bool(pred),
                    "confidence": float(prob[1] if len(prob) > 1 else prob[0])
                }
                results.append(result)

                if pred:
                    ai_paragraphs.append(essay)

        # Save AI paragraphs
        if ai_paragraphs:
            with open(app.config['OUTPUT_FILE'], 'w', encoding='utf-8') as f:
                f.write("\n\n".join(ai_paragraphs))

        # Calculate stats
        stats = {
            "total": len(results),
            "ai_count": len(ai_paragraphs),
            "ai_percentage": f"{len(ai_paragraphs) / len(results):.2%}"
        }

        return jsonify({
            "success": True,
            "stats": stats,
            "results": results
        })

    except Exception as e:
        return jsonify({
            "error": f"Processing failed: {str(e)}"
        }), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)