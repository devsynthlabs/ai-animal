"""
AI Animal Type Classification System
Main Flask Application
"""

import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

from config import Config
from gemini_analyzer import GeminiAnalyzer
from atc_scoring import ATCScorer
from bpa_integration import BPAIntegration

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# Ensure upload folder exists
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

# Initialize components
analyzer = None
scorer = ATCScorer()
bpa_client = BPAIntegration()

# Store results in memory (in production, use database)
analysis_results = {}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def get_analyzer():
    """Get or initialize the Gemini analyzer."""
    global analyzer
    if analyzer is None:
        try:
            analyzer = GeminiAnalyzer()
        except ValueError as e:
            return None, str(e)
    return analyzer, None


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html', 
                         results=analysis_results,
                         bpa_configured=bpa_client.is_configured)


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle image upload and analysis."""
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Use PNG, JPG, JPEG, or WebP'}), 400
    
    # Save the uploaded file
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{filename}"
    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    # Get analyzer
    gemini, error = get_analyzer()
    if error:
        # Remove uploaded file since we can't process it
        os.remove(filepath)
        return jsonify({'error': f'API Key Error: {error}. Please add your GEMINI_API_KEY to the .env file.'}), 400
    
    if gemini is None:
        os.remove(filepath)
        return jsonify({'error': 'Gemini API key not configured. Create a .env file with GEMINI_API_KEY=your_key'}), 400
    
    try:
        # Analyze the image
        print(f"[DEBUG] Analyzing image: {filepath}")
        result = gemini.analyze_image(filepath)
        print(f"[DEBUG] Analysis result: {result}")
        
        if result.get('error'):
            return jsonify({'error': result.get('message', 'Analysis failed')}), 500
        
        # Format the report
        report = scorer.format_report(result)
        report['image_path'] = filename
        
        # Store the result
        report_id = report['report_id']
        analysis_results[report_id] = report
        
        return jsonify({
            'success': True,
            'report_id': report_id,
            'report': report
        })
        
    except Exception as e:
        import traceback
        print(f"[ERROR] Upload failed: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/results/<report_id>')
def view_result(report_id):
    """View a specific analysis result."""
    report = analysis_results.get(report_id)
    if not report:
        flash('Report not found', 'error')
        return redirect(url_for('index'))
    
    return render_template('results.html', report=report)


@app.route('/api/results/<report_id>')
def get_result_api(report_id):
    """Get analysis result as JSON."""
    report = analysis_results.get(report_id)
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    return jsonify(report)


@app.route('/export/<report_id>')
def export_result(report_id):
    """Export result for BPA."""
    report = analysis_results.get(report_id)
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    
    bpa_data = scorer.export_for_bpa(report)
    return jsonify(bpa_data)


@app.route('/submit-bpa/<report_id>', methods=['POST'])
def submit_to_bpa(report_id):
    """Submit result to BPA."""
    report = analysis_results.get(report_id)
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    
    # Get additional metadata from request
    data = request.get_json() or {}
    
    # Format and submit
    bpa_data = scorer.export_for_bpa(report)
    submission = bpa_client.format_submission(
        bpa_data,
        animal_id=data.get('animal_id'),
        farmer_id=data.get('farmer_id'),
        location=data.get('location')
    )
    
    result = bpa_client.submit_classification(submission)
    return jsonify(result)


@app.route('/history')
def history():
    """View analysis history."""
    return render_template('history.html', results=analysis_results)


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  AI Animal Type Classification System")
    print("="*60)
    print("\n🚀 Starting server at http://localhost:5000")
    print("\n📋 Before running:")
    print("   1. Create a .env file with your GEMINI_API_KEY")
    print("   2. Get your API key from: https://aistudio.google.com/apikey")
    print("\n" + "="*60 + "\n")
    
    app.run(debug=True, port=5000)
