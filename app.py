from flask import Flask, request, jsonify, render_template
import csv
import PyPDF2
import google.generativeai as palm

app = Flask(__name__)

# Configure the Gemini API with your actual API key
palm.configure(api_key='Replace with your actual Gemini API key')  

# Replace with your CSV file path
csv_file_path = 'sample data-50.csv'  # Ensure this path is correct
pdf_path = 'STUDENT CODE OF CONDUCT.pdf'  # Path to the PDF file

# Function to extract text from PDF
def extract_pdf_text(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
    return text

# Extract text from the PDF once and store it
pdf_text = extract_pdf_text(pdf_path)

# Function to search by name or ID in CSV
def search_csv(file_path, search_value, search_by):
    try:
        with open(file_path, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if search_by == 'id' and row.get('id') == search_value:
                    return row
                elif search_by == 'name' and (row.get('first_name') == search_value or row.get('last_name') == search_value):
                    return row
    except FileNotFoundError:
        print("Error: File not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return None

# Simple keyword-based response generator for PDF
def search_pdf_content(query):
    if query.lower() in pdf_text.lower():
        # If the query is found in the text, return a snippet of the content around the match
        start_idx = pdf_text.lower().find(query.lower())
        snippet = pdf_text[max(0, start_idx - 100):start_idx + 300]  # Return 100 chars before and 300 after
        return snippet
    else:
        return None  # Return None if no match is found

# Function to generate a response using the Gemini API
def generate_gemini_response(user_input):
    prompt = f"The following is the content of the Student Code of Conduct:\n\n{pdf_text}\n\nUser: {user_input}\nBot:"
    try:
        response = palm.generate_text(
            model='models/text-bison-001',
            prompt=prompt,
            temperature=0.7,
            max_output_tokens=256
        )
        return response.result
    except Exception as e:
        return f"Error using Gemini API: {str(e)}"

# Route to render the chat interface
@app.route('/')
def index():
    return render_template('chatbot.html')

# Search route to handle user queries for student data
@app.route('/search', methods=['POST'])
def search():
    user_query = request.form.get('user_query')
    search_type = request.form.get('search_type')  # Get the selected search type (id or name)

    if not user_query:
        return jsonify("No query provided"), 400

    # Perform the search
    result = search_csv(csv_file_path, user_query, search_type)

    if result:
        return jsonify(result), 200
    else:
        return jsonify("No matching entry found."), 404

# Chat route to handle user questions about the code of conduct
@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.form.get('user_input')
    if not user_input:
        return jsonify("No input provided."), 400

    # First, try searching the PDF content locally
    pdf_response = search_pdf_content(user_input)

    if pdf_response:
        return jsonify(f"Found in PDF: {pdf_response}"), 200
    else:
        # If no match is found in the PDF, use Gemini API for a more intelligent response
        gemini_response = generate_gemini_response(user_input)
        return jsonify(f"Gemini Response: {gemini_response}"), 200

if __name__ == '__main__':
    app.run(debug=True)

