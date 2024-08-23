import dotenv
import os
import uuid
import mysql.connector
import pathlib
import requests
import google.auth.transport.requests
import pip._vendor.cachecontrol as cachecontrol
import time
import redis
from authlib.integrations.flask_client import OAuth
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from functools import wraps
from flask import Flask, abort, jsonify, redirect, request, session, render_template, url_for
from flask_session import Session

dotenv.load_dotenv()
if not os.getenv('FLASK_SECRET_KEY'):
    print('Please set FLASK_SECRET_KEY in .env file.')
    exit(1)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# OAUTH CONFIG
oauth = OAuth(app)
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'openid profile email'},
    jwks_uri = "https://www.googleapis.com/oauth2/v3/certs",
    clock_skew_in_seconds=10
)

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')

def login_is_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if 'email' not in session:  # Check if the user is logged in
            return abort(401)  # If not, return 401 Unauthorized
        else:
            return function(*args, **kwargs)
    return wrapper

@app.route('/quiz')
@login_is_required # Decorator to check if the user is logged in
def quiz():
    user_name = session.get('name')
    return render_template("quiz.html", user_name=user_name)

@app.route('/master_index')
@login_is_required
def master_index():
    user_name = session.get('name')
    return render_template("master_index.html", user_name=user_name)
    
# Redirect user to Google content screen
@app.route('/login')
def login():
    google = oauth.create_client('google') # Create/get the google client above
    redirect_uri = url_for('authorize', _external=True)
    session.pop('is_faculty', None) # Remove the faculty flag if it exists since this is regular student login
    return oauth.google.authorize_redirect(redirect_uri)

# Redirect faculty to Google content screen
@app.route('/faculty_redirect')
def faculty_redirect():
    # List of allowed faculty emails
    allowed_faculty_emails = [
        "colemanb@moravian.edu",
        "drabicj@moravian.edu",
        "romerom@moravian.edu",
        "garciar03@moravian.edu"
    ]

    # If the user's email is not in the allowed list, abort with a 403 Forbidden error
    if session.get('email') not in allowed_faculty_emails:
        return abort(403)
    return redirect('/master_index')

@app.route('/faculty_login')
def faculty_login():
    google = oauth.create_client('google') # Create/get the google client above
    redirect_uri = url_for('authorize', _external=True)
    session['is_faculty'] = True  # Set a flag to identify faculty users
    return oauth.google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
   
    google = oauth.create_client('google') # Create/get the google client above
    token = oauth.google.authorize_access_token()
    resp = oauth.google.get('userinfo')
    user_info = resp.json()
    # Store the user's email, google_id, and name in the session
    session['email'] = user_info['email']
    session['name'] = user_info['name']
    session['google_id'] = user_info['id']

    cursor, cnx = connectToMySQL()

    try:
        # Check if user already exists in the session table
        query_check = "SELECT * FROM session WHERE email = %s"
        cursor.execute(query_check, (session['email'],))
        existing_user = cursor.fetchone()  # Fetch the first row

        if existing_user:
            # Updates the existing user if necessary
            query_update = "UPDATE session SET name = %s WHERE email = %s"
            cursor.execute(query_update, (session['name'], session['email']))
            cnx.commit()
        else:
            # Insert the new user if they do not exist in the session table
            query_insert = "INSERT INTO session (user_id, name, email) VALUES (%s, %s, %s)"
            cursor.execute(query_insert, (session['google_id'], session['name'], session['email']))
            cnx.commit()

    except mysql.connector.Error as err:
        print(f"Error during login: {err}")
        cnx.rollback()  # Rollback the transaction in case of error
        return abort(500)

    finally:
        cursor.close()
        cnx.close()

    # Redirect based on the user type (faculty or student)
    if session.get('is_faculty'):
        return redirect('/faculty_redirect')
    else:
        return redirect('/quiz')

# Clear login session from the user
@app.route('/logout') 
def logout():
    for key in list(session.keys()): # Clear all keys from the session data
        session.pop(key)
    return redirect('/')

# Default route to render index.html
@app.route('/')
def index():
    return render_template("index.html")
    
# Gets all the questions from the database
@app.route('/getQuestions')
def get_questions():
    MYSQL_DB = os.getenv('MYSQL_DB')
    '''
    Returns the questions from the database.
    '''
    cursor, connection = connectToMySQL()
    use_db = f"USE {MYSQL_DB};"
    select = ""

    if request.args.get('group') == "1":
        select = "SELECT * FROM questions WHERE question_num = 1 ORDER BY group_num;"
            
    elif request.args.get('group') == "2":
        select = "SELECT * FROM questions WHERE question_num = 2 ORDER BY group_num;"
        
    elif request.args.get('group') == "3":
        select = "SELECT * FROM questions WHERE question_num = 3 ORDER BY group_num;"
            
    elif request.args.get('group') == "4":
        select = "SELECT * FROM questions WHERE question_num = 4 ORDER BY group_num;"
            
    else:
        select = "SELECT * FROM questions WHERE question_num = 5 ORDER BY group_num;"
            
    cursor.execute(use_db)
    cursor.execute(select)
        
    questions = cursor.fetchall()
    
    cursor.close()
    connection.close()

    return jsonify(questions)
    
# Stores the user's scores in the database
@app.route('/storeResult', methods=['POST'])
def store_result():
    '''
    Stores the user's color result in the database.
    '''
    email = session['email']
    data = request.get_json()
    results = data['results']

    cursor, connection = connectToMySQL()

    # MySQL query to insert or update each group score
    use_db = "USE TrueColors;"
    cursor.execute(use_db)

    # Retrieve the highest test_id and increment it by 1
    cursor.execute("SELECT MAX(test_id) FROM responses")
    last_test_id = cursor.fetchone()[0]
    new_test_id = 1 if last_test_id is None else last_test_id + 1

    for result in results:
        question_num = result['question_num']
        group_num = result['group_num']
        score = result['score']

        select_query = """
        SELECT * FROM responses 
        WHERE user_id = %s AND test_id = %s AND question_num = %s AND group_num = %s;
        """
        
        test_id = """SELECT test_id FROM response_flags WHERE user_id = %s;"""

        cursor.execute(select_query, (email, new_test_id, question_num, group_num))
        existing_record = cursor.fetchone()

        if existing_record:
            update_query = """
            UPDATE responses 
            SET score = %s 
            WHERE user_id = %s AND test_id = %s AND question_num = %s AND group_num = %s;
            """
            cursor.execute(update_query, (score, email, new_test_id, question_num, group_num))
        else:
            insert_query = """
            INSERT INTO responses (user_id, test_id, question_num, group_num, score) 
            VALUES (%s, %s, %s, %s, %s);
            """
            cursor.execute(insert_query, (email, new_test_id, question_num, group_num, score))

    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({'message': 'Scores updated successfully'}), 200
    
@app.route('/save_location', methods=['POST'])
def save_location():
    '''
    Saves the user's quiz location to the database.
    '''
    location = request.json.get('location')
    if not location:
        return "No location provided.", 400

    email = session['email']
    
    cursor, connection = connectToMySQL()
    
    # MySQL queries
    use_db = "USE TrueColors;"
    insert_location = """
    INSERT INTO quiz (user_id, test_id, description)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE description = VALUES(description);
    """

    cursor.execute(use_db)

    # Retrieve the highest test_id and increment it by 1
    cursor.execute("SELECT MAX(test_id) FROM quiz")
    last_test_id = cursor.fetchone()[0]
    new_test_id = 1 if last_test_id is None else last_test_id + 1

    cursor.execute(insert_location, (email, new_test_id, location))

    connection.commit()
    cursor.close()
    connection.close()

    return "Location saved successfully.", 200 

# Fetches all scores from a specific email
def fetch_all_scores_from_email(email):
    '''
    Fetches all scores from the database and calculates the color scores for each user.
    '''
    cursor, connection = connectToMySQL()
    use_db = "USE TrueColors;"
    cursor.execute(use_db)
    cursor.execute("""
        SELECT user_id, test_id, question_num, group_num, score
        FROM responses
        WHERE user_id = %s 
        ORDER BY user_id, test_id, question_num, group_num
    """, (email,))

    rows = cursor.fetchall()
    connection.close()

    result = create_score_dictionary(rows)
    return result

# Endpoint to fetch all scores from the database
@app.route('/fetch_data')
def fetch_all_scores():
    '''
    Fetches all scores from the database and calculates the color scores for each user.
    '''
    cursor, connection = connectToMySQL()
    use_db = "USE TrueColors;"
    cursor.execute(use_db)
    cursor.execute("""
        SELECT user_id, test_id, question_num, group_num, score
        FROM responses
        ORDER BY user_id, test_id, question_num, group_num
    """)

    rows = cursor.fetchall()
    connection.close()
    result = create_score_dictionary(rows)
    return jsonify(result)

# Creates a dictionary of scores based on the rows passed in the parameter
def create_score_dictionary(rows):
    # Initialize a dictionary to store scores for each (user_id, test_id) combination
    user_test_scores = {}

    # Populate the dictionary with scores
    for row in rows:
        user_id = row[0]
        test_id = row[1]
        key = (user_id, test_id)

        if key not in user_test_scores:
            user_test_scores[key] = {'score_orange': 0, 'score_blue': 0, 'score_gold': 0, 'score_green': 0}
        
        q_num = row[2]
        g_num = row[3]
        score = row[4]

        # Calculate scores based on the given formula
        if q_num == 1 and g_num == 1:
            user_test_scores[key]['score_orange'] += score
        elif q_num == 2 and g_num == 4:
            user_test_scores[key]['score_orange'] += score
        elif q_num == 3 and g_num == 3:
            user_test_scores[key]['score_orange'] += score
        elif q_num == 4 and g_num == 2:
            user_test_scores[key]['score_orange'] += score
        elif q_num == 5 and g_num == 3:
            user_test_scores[key]['score_orange'] += score
        
        if q_num == 1 and g_num == 3:
            user_test_scores[key]['score_blue'] += score
        elif q_num == 2 and g_num == 2:
            user_test_scores[key]['score_blue'] += score
        elif q_num == 3 and g_num == 2:
            user_test_scores[key]['score_blue'] += score
        elif q_num == 4 and g_num == 3:
            user_test_scores[key]['score_blue'] += score
        elif q_num == 5 and g_num == 2:
            user_test_scores[key]['score_blue'] += score

        if q_num == 1 and g_num == 2:
            user_test_scores[key]['score_gold'] += score
        elif q_num == 2 and g_num == 3:
            user_test_scores[key]['score_gold'] += score
        elif q_num == 3 and g_num == 1:
            user_test_scores[key]['score_gold'] += score
        elif q_num == 4 and g_num == 1:
            user_test_scores[key]['score_gold'] += score
        elif q_num == 5 and g_num == 4:
            user_test_scores[key]['score_gold'] += score

        if q_num == 1 and g_num == 4:
            user_test_scores[key]['score_green'] += score
        elif q_num == 2 and g_num == 1:
            user_test_scores[key]['score_green'] += score
        elif q_num == 3 and g_num == 4:
            user_test_scores[key]['score_green'] += score
        elif q_num == 4 and g_num == 4:
            user_test_scores[key]['score_green'] += score
        elif q_num == 5 and g_num == 1:
            user_test_scores[key]['score_green'] += score

    # Convert the dictionary to a list of lists containing only the scores
    result = [[value['score_orange'], value['score_blue'], value['score_gold'], value['score_green']] for value in user_test_scores.values()]
    return result

# Fetches the session data from the database
@app.route('/fetch_session_data')
def fetch_session_data():
    '''
    Grabs the session data from the database and returns it.
    '''
    cursor, connection = connectToMySQL()
    use_db = "USE TrueColors;"
    cursor.execute(use_db)
    query = query = """
    SELECT 
        s.name, 
        s.email,
        MAX(q.time_stamp) AS latest_attempt,
        COUNT(q.test_id) AS attempt_count
    FROM 
        session s
    LEFT JOIN 
        quiz q ON s.email = q.user_id
    GROUP BY 
        s.name, s.email;
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    connection.close()
    return jsonify(rows)

@app.route('/fetch_user_info')
def fetch_user_info():
    email = request.args.get('email')
    try:
        scores = fetch_all_scores_from_email(email)
        cursor, connection = connectToMySQL()
        use_db = "USE TrueColors;"
        cursor.execute(use_db)
        cursor.execute("SELECT name, email FROM session;")
        session_data = cursor.fetchall()

        # Fetch timestamps for each test attempt

        cursor.execute("SELECT user_id, test_id, time_stamp, description FROM quiz WHERE user_id = %s ORDER BY test_id, user_id;", (email,))
        quiz_data = cursor.fetchall()
        quiz_data.reverse()  # Reverse the list to display the most recent test first
        
        connection.close()

        all_data = []
        if not session_data:
            return jsonify({"error": "No session data found"}), 500

        for idx, score in enumerate(scores):
            percentages = [
                {
                    'color': 'Orange',
                    'score': score[0],
                    'percentage': round((score[0] / 50) * 100, 1)  # Calculate and round percentage
                },
                {
                    'color': 'Blue',
                    'score': score[1],
                    'percentage': round((score[1] / 50) * 100, 1)
                },
                {
                    'color': 'Gold',
                    'score': score[2],
                    'percentage': round((score[2] / 50) * 100, 1)
                },
                {
                    'color': 'Green',
                    'score': score[3],
                    'percentage': round((score[3] / 50) * 100, 1)
                }
            ]

            # Find the corresponding timestamp for the test attempt
            timestamp = quiz_data[idx][2].strftime('%m-%d-%Y %H:%M:%S')

            # Append session data and percentages to the response list
            all_data.append({
                'scores': percentages,
                'timestamp': timestamp,  # Include formatted timestamp
                'description': quiz_data[idx][3]
            })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
    return jsonify(all_data)


@app.route('/student_data/<email>/<name>')
@login_is_required
def student_data(email, name):
    '''
    Fetches and displays data for a specific student based on their email.
    '''
    try:
        # Fetch all data from the /fetch_user_info endpoint
        response = requests.get(url_for('fetch_user_info', email=email, _external=True))
        
        all_data = response.json()

        # Filter data for the specific student
        all_scores = []
        for data in all_data:
            if not data:
                return render_template('student_data.html', data=[], student_email=email, student_name=name)
            all_scores.append(data['scores'])
            
        all_scores.reverse()  # Reverse the list to display the most recent test first
        return render_template('student_data.html', data=all_scores, all_data=all_data, student_email=email, student_name=name) #Index all_scores by a number to get that test number

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
def connectToMySQL():
    '''
    Connects to MySQL and returns a cursor and connection object.
    '''
    MYSQL_USERNAME = os.getenv('MYSQL_USERNAME')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
    MYSQL_HOST = os.getenv('MYSQL_HOST')
    MYSQL_DB = os.getenv('MYSQL_DB')

    cnx = mysql.connector.connect(user=MYSQL_USERNAME, password=MYSQL_PASSWORD,
                                  host=MYSQL_HOST,
                                  database=MYSQL_DB)
    #Tried with user = root, password = password, host = most recent AWS ip
    cursor = cnx.cursor()
    return cursor, cnx

if __name__ == '__main__':
    app.run(debug=True, port=8000, host="0.0.0.0")
