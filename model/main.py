from flask import Flask, render_template, redirect, send_from_directory
import subprocess
import threading
import time
import os

app = Flask(__name__)

# Global variable to track if Gradio is running
gradio_process = None
gradio_started = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

@app.route('/remedies')
def remedies():
    return render_template('remedies.html')

@app.route('/explore')
def explore():
    return render_template('explore.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/gradio')
def start_gradio():
    global gradio_process, gradio_started
    
    # Only start Gradio if it's not already running
    if not gradio_started:
        def run_gradio():
            global gradio_process, gradio_started
            try:
                # Start the Gradio app
                gradio_process = subprocess.Popen(['python', 'app.py'])
                gradio_started = True
                print("🤖 MedMind Gradio chatbot started!")
            except Exception as e:
                print(f"Error starting Gradio: {e}")
        
        # Start Gradio in a separate thread
        gradio_thread = threading.Thread(target=run_gradio)
        gradio_thread.daemon = True
        gradio_thread.start()
        
        # Wait a moment for Gradio to start
        time.sleep(2)
    
    # Redirect to the Gradio interface
    return redirect('http://localhost:7860')

# Serve images from the images folder
@app.route('/images/<filename>')
def serve_images(filename):
    return send_from_directory('../images', filename)

if __name__ == "__main__":
    print("🌐 Starting MedMind Flask Server...")
    print("📋 Landing pages will be available at http://localhost:5000")
    print("🤖 Chatbot will start only when accessed via /gradio")
    
    # Start Flask (NO automatic Gradio startup)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
