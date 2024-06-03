from flask import Flask, make_response, request, jsonify, redirect, send_from_directory, url_for, render_template
import random
import secrets
import string
import os
import json

app = Flask(__name__)

invitation_codes = {
    "Axasdf2a": {"type": 0, "status": 0, "name": "Elon Musk"}
}
## Type: 0->无干扰 1->有干扰
## status: 0->无任何操作 1->已签名 2->已完成

# Configs
question_num = 10
admin_id = 'some_username'
admin_pass = 'some_password'
admin_token = ''


# Utils
def save_file(directory, filename, file):
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)
    file.save(filepath)

def generateToken(length=8):
    characters = string.ascii_letters + string.digits
    token = ''.join(random.choice(characters) for _ in range(length))
    return token

def generate_questions(num_questions=10):
    colors = ["red", "blue", "green", "yellow", "orange", "purple", "black", "white"]
    questions = []
    
    for _ in range(num_questions):
        correct_color = random.choice(colors)
        options = random.sample(colors, 4)
        
        if correct_color not in options:
            options[random.randint(0, 3)] = correct_color
        
        interference = correct_color
        while interference == correct_color:
            interference = random.choice(colors)
        
        question = {
            "options": options,
            "correct": correct_color,
            "interference": interference
        }
        
        questions.append(question)
    
    return questions

# Private APIs
@app.route('/api/login', methods=['POST'])
def loginapi():
    try:
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return jsonify({"error": "Username and password are required."}), 400

        if username == admin_id and password == admin_pass:
            global admin_token
            admin_token = secrets.token_urlsafe(16)
            resp = make_response(redirect('/admin'))
            resp.set_cookie('token', admin_token)
            return resp
        else:
            return jsonify({"error": "Invalid username or password. Please try again."}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/setQuestionNum', methods=['POST'])
def setQuestionNumAPI():
    try:
        num = request.form.get('num')
        token = request.cookies.get('token')

        if not num or not num.isdigit():
            return jsonify({"error": "Invalid or missing 'num' parameter."}), 400

        if token == admin_token:
            global question_num
            question_num = int(num)
            return "1"
        return "0"
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/getQuestionNum', methods=['GET'])
def getQuestionNum():
    try:
        token = request.cookies.get('token')
        if token == admin_token:
            return question_num
        return jsonify([]), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/getList', methods=['GET'])
def getListAPI():
    try:
        token = request.cookies.get('token')
        if token == admin_token:
            return jsonify(invitation_codes)
        return jsonify([]), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/UpdateInvitation', methods=['POST'])
def updateInvitationAPI():
    try:
        invitationCode = request.form.get('invitationCode')
        type = request.form.get('type')
        status = request.form.get('status')
        name = request.form.get('name')
        token = request.cookies.get('token')

        if not invitationCode or not type or not status or not name:
            return jsonify({"error": "All fields are required."}), 400

        if token == admin_token:
            invitation_codes[invitationCode] = {"type": type, "status": status, "name": name}
            return "1"
        return "0"
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/newInvitation', methods=['POST'])
def newInvitationAPI():
    try:
        type = request.form.get('type')
        status = request.form.get('status')
        name = request.form.get('name')
        token = request.cookies.get('token')

        if not type or not status or not name:
            return jsonify({"error": "All fields are required."}), 400

        if token == admin_token:
            new_invitation_code = generateToken(8)
            while new_invitation_code in invitation_codes:
                new_invitation_code = generateToken(8)
            invitation_codes[new_invitation_code] = {"type": type, "status": status, "name": name}
            return new_invitation_code
        return "-1"
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/delInvitation', methods=['POST'])
def delInvitationAPI():
    try:
        invitationCode = request.form.get('invitationCode')
        token = request.cookies.get('token')

        if not invitationCode:
            return jsonify({"error": "Invitation code is required."}), 400

        if token == admin_token:
            if invitationCode in invitation_codes:
                del invitation_codes[invitationCode]
                return "1"
        return "0"
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Public APIs
@app.route('/api/check_invitation_code', methods=['POST'])
def check_invitation_code():
    data = request.get_json()
    invitation_code = data.get('invitation_code')
    if invitation_code in invitation_codes and invitation_codes[invitation_code]["status"] == 0:
        return jsonify({"name": invitation_codes[invitation_code]["name"], "type": invitation_codes[invitation_code]["type"], "status": invitation_codes[invitation_code]["status"]}), 200
    else:
        return jsonify({"error": "Invalid invitation code"}), 400

@app.route('/api/get_questions/<invitation_code>', methods=['GET'])
def get_questions(invitation_code):
    if invitation_code not in invitation_codes or invitation_codes[invitation_code]["status"] > 0:
        return jsonify({"error": "Invalid invitation code"}), 400
    sign_dir = os.path.join('./data', invitation_code)
    sign_path = os.path.join(sign_dir, "sign.png")
    if not os.path.exists(sign_path):
        return jsonify({"error": "User haven't signed yet"}), 400
    question_list = generate_questions(question_num)  
    invitation_codes[invitation_code]["status"] = 1
    directory = os.path.join('./data', invitation_code)
    question_path = os.path.join(directory, "questions.json")
    os.makedirs(directory, exist_ok=True)
    with open(question_path, 'w') as f:
        json.dump({'type': invitation_codes[invitation_code]['type'], 'name': invitation_codes[invitation_code]['name'], 'data': question_list}, f)
    return jsonify(question_list)

@app.route('/api/submit_answers/<invitation_code>', methods=['POST'])
def submit_answers(invitation_code):
    print(invitation_code)
    print(invitation_codes[invitation_code]["status"])
    if invitation_code not in invitation_codes or invitation_codes[invitation_code]["status"] != 1:
        return jsonify({"error": "Invalid invitation code"}), 400
    data = request.get_json()
    print(data)
    if not data or 'answers' not in data:
        return jsonify({"error": "Missing answers in request"}), 400

    answers = data.get('answers')
    directory = os.path.join('./data', invitation_code)
    filepath = os.path.join(directory, 'answer.json')

    os.makedirs(directory, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(answers, f)
    
    recording_path = os.path.join(directory, "recording.webm")
    if os.path.exists(recording_path):
        invitation_codes[invitation_code]["status"] = 2

    return jsonify({"message": "Answers submitted successfully"}), 200

@app.route('/api/submit_recording/<invitation_code>', methods=['POST'])
def submit_recording(invitation_code):
    if invitation_code not in invitation_codes or invitation_codes[invitation_code]["status"] != 1:
        return jsonify({"error": "Invalid invitation code"}), 400

    recording = request.files.get('recording')
    if not recording or not recording.filename.endswith('.webm'):
        return jsonify({"error": "Invalid recording file"}), 400

    directory = os.path.join('./data', invitation_code)
    save_file(directory, 'recording.webm', recording)

    answer_path = os.path.join(directory, "answer.json")
    if os.path.exists(answer_path):
        invitation_codes[invitation_code]["status"] = 2

    return jsonify({"message": "Recording submitted successfully"})

@app.route('/api/submit_signature/<invitation_code>', methods=['POST'])
def submit_signature(invitation_code):
    if invitation_code not in invitation_codes or invitation_codes[invitation_code]["status"] > 0:
        return jsonify({"error": "Invalid invitation code"}), 400

    signature = request.files.get('signature')
    if not signature or not signature.filename.endswith('.png'):
        return jsonify({"error": "Invalid signature file"}), 400

    directory = os.path.join('./data', invitation_code)
    save_file(directory, 'sign.png', signature)

    return jsonify({"message": "Signature submitted successfully"}), 200


# Public Pages
@app.route('/')
def root():
    user_agent = request.headers.get('User-Agent')
    if 'Mobile' in user_agent:
        return redirect('/mobile-alert')
    return send_from_directory("pages", 'index.html')
@app.route('/quizz')
def quizz():
    user_agent = request.headers.get('User-Agent')
    if 'Mobile' in user_agent:
        return redirect('/mobile-alert')
    return send_from_directory("pages", 'quizz.html')
@app.route('/finished')
def finished():
    user_agent = request.headers.get('User-Agent')
    if 'Mobile' in user_agent:
        return redirect('/mobile-alert')
    return send_from_directory("pages", 'finished.html')
@app.route('/mobile-alert')
def mobile_alert():
    return send_from_directory("pages", 'mobile-alert.html')


# Private Pages
@app.route('/admin')
def admin():
    token = request.cookies.get('token')
    if token == admin_token:
        return send_from_directory("pages", "admin.html")
    else:
        return redirect('/login')
    
@app.route('/login')
def login():
    return send_from_directory("pages", "login.html")

# Resources
@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    app.run(debug=True)