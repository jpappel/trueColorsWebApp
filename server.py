from flask import Flask, abort, jsonify, redirect, request, session, render_template
from dotenv import load_dotenv
import dotenv
import os
import uuid
import mysql.connector
import pathlib
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2 import id_token
import google.auth.transport.requests
import pip._vendor.cachecontrol as cachecontrol  # Import cachecontrol

dotenv.load_dotenv()
if not os.getenv('FLASK_SECRET_KEY'):
    print('Please set FLASK_SECRET_KEY in .env file.')
    exit(1)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Only for testing purposes

# Load environment variables from .env file
load_dotenv()

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, 'client_secrets.json')

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=['https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email', 'openid'],
    redirect_uri='http://127.0.0.1:8000/callback')

def login_is_required(function):
    def wrapper(*args, **kwargs):
        if 'google_id' not in session:  # Check if the user is logged in
            return abort(401)  # If not, return 401 Unauthorized
        else:
            return function(*args, **kwargs)
        
    return wrapper

@app.route('/quiz')
@login_is_required
def quiz():
    user_name = session.get('name')
    return render_template("quiz.html", user_name=user_name)
    
# Redirect user to Google content screen
@app.route('/login')
def login():
    authorization_url, state = flow.authorization_url()
    session['state'] = state
    return redirect(authorization_url)

# Receive data from Google endpoint
@app.route('/callback')
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session['state'] == request.args['state']:
        return abort(500)  # State does not match!
    
    credentials = flow.credentials
    request_session = flow.authorized_session()
    cached_session = cachecontrol.CacheControl(request_session)  # Use cachecontrol
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials.id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID)
    
    session['google_id'] = id_info.get('sub')
    session['name'] = id_info.get('name')
    session['email'] = id_info.get('email')
    
    cursor, cnx = connectToMySQL()
    
    try:
        # Check if user already exists in the session table
        query_check = "SELECT * FROM session WHERE email = %s"
        cursor.execute(query_check, (session['email'],))
        existing_user = cursor.fetchone() # Fetch the first row 
        
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
        
    return redirect('/quiz')

# Clear login session from the user
@app.route('/logout') 
def logout():
    session.clear()
    return redirect('/')

# Route to get session data
@app.route('/session_data')
def session_data():
    return jsonify(dict(session))

@app.route('/')
def index():
    return render_template("index.html")
    
def getId():
    if 'uuid' not in session:
        id = str(uuid.uuid4())
        session['uuid'] = id
    else:
        id = session['uuid']
    return id
    
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
        select = "SELECT * FROM ordered_questions WHERE question_num = 1;"
            
    elif request.args.get('group') == "2":
        select = "SELECT * FROM ordered_questions WHERE question_num = 2;"
        
    elif request.args.get('group') == "3":
        select = "SELECT * FROM ordered_questions WHERE question_num = 3;"
            
    elif request.args.get('group') == "4":
        select = "SELECT * FROM ordered_questions WHERE question_num = 4;"
            
    else:
        select = "SELECT * FROM ordered_questions WHERE question_num = 5;"
            
    cursor.execute(use_db)
    cursor.execute(select)
        
    questions = cursor.fetchall()
    print(jsonify(questions))
    
    cursor.close()
    connection.close()

    return jsonify(questions)
    
@app.route('/storeResult', methods=['POST'])
def store_result():
    '''
    Stores the user's color result in the database.
    '''
    id = getId()
    data = request.get_json()
    results = data['results']
    print(results)

    cursor, connection = connectToMySQL()

    # MySQL query to insert or update each group score
    use_db = "USE TrueColors;"
    cursor.execute(use_db)

    # Retrieve the highest test_id and increment it by 1
    cursor.execute("SELECT MAX(test_id) FROM responses")
    last_test_id = cursor.fetchone()[0]
    new_test_id = 1 if last_test_id is None else last_test_id + 1

    for result in results:
        print(result)
        question_num = result['question_num']
        group_num = result['group_num']
        score = result['score']

        select_query = """
        SELECT * FROM responses 
        WHERE user_id = %s AND test_id = %s AND question_num = %s AND group_num = %s;
        """
        # UPDATE TEST ID TO NOT JUST BE 1 
        cursor.execute(select_query, (id, new_test_id, question_num, group_num)) # 1 is the test Id, update when we figure that out
        existing_record = cursor.fetchone()

        if existing_record:
            update_query = """
            UPDATE responses 
            SET score = %s 
            WHERE user_id = %s AND test_id = %s AND question_num = %s AND group_num = %s;
            """
            # UPDATE TEST ID TO NOT JUST BE 1
            cursor.execute(update_query, (score, id, new_test_id, question_num, group_num)) # 1 is the test Id, update when we figure that out
        else:
            insert_query = """
            INSERT INTO responses (user_id, test_id, question_num, group_num, score) 
            VALUES (%s, %s, %s, %s, %s);
            """
            # UPDATE TEST ID TO NOT JUST BE 1
            cursor.execute(insert_query, (id, new_test_id, question_num, group_num, score)) # 1 is the test Id, update when we figure that out

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

    id = getId()
    
    cursor, connection = connectToMySQL()
    
    # MySQL queries
    use_db = "USE TrueColors;"
    insert_location = """
    INSERT INTO quiz (user_id, test_id, description)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE description = VALUES(description);
    """

    cursor.execute(use_db)
    cursor.execute(insert_location, (id, 1, location)) # Have to update test_id from 1 to autoincrement

    connection.commit()
    cursor.close()
    connection.close()

    return "Location saved successfully.", 200 

def fetch_all_scores():
    '''
    Fetches all scores from the database and calculates the color scores for each user.
    '''
    cursor, connection = connectToMySQL()
    use_db = "USE TrueColors;"
    cursor.execute(use_db)
    cursor.execute("""
        SELECT user_id, test_id, question_num, group_num, score
        FROM responses  -- Change this to your actual table name
        ORDER BY user_id, test_id, question_num, group_num
    """)

    rows = cursor.fetchall()
    connection.close()

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
    print("Color Results", result)
    return result


@app.route('/fetch_data')
def fetch_data():
    '''
    Uses the fetch_all_scores function to return all scores.
    '''
    try:
        scores = fetch_all_scores()
        print("Scores", scores)
        return jsonify(scores)
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
