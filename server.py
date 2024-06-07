from flask import Flask, jsonify, request, render_template, session
import dotenv
import os
import uuid
import mysql.connector

dotenv.load_dotenv()
if not os.getenv('FLASK_SECRET_KEY'):
    print('Please set FLASK_SECRET_KEY in .env file.')
    exit(1)

app = Flask(__name__)
app.secret_key = 'secret'

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
        cursor.execute(select_query, (id, 1, question_num, group_num)) # 1 is the test Id, update when we figure that out
        existing_record = cursor.fetchone()

        if existing_record:
            update_query = """
            UPDATE responses 
            SET score = %s 
            WHERE user_id = %s AND test_id = %s AND question_num = %s AND group_num = %s;
            """
            # UPDATE TEST ID TO NOT JUST BE 1
            cursor.execute(update_query, (score, id, 1, question_num, group_num)) # 1 is the test Id, update when we figure that out
        else:
            insert_query = """
            INSERT INTO responses (user_id, test_id, question_num, group_num, score) 
            VALUES (%s, %s, %s, %s, %s);
            """
            # UPDATE TEST ID TO NOT JUST BE 1
            cursor.execute(insert_query, (id, 1, question_num, group_num, score)) # 1 is the test Id, update when we figure that out

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

@app.route('/fetch_data')
def fetch_data():
    '''
    Fetches data from the database and returns it as JSON.
    '''
    cursor, connection = connectToMySQL()
    select = "SELECT result_color, COUNT(*) AS count FROM user_colors GROUP BY result_color"
    cursor.execute(select)
    data = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(data)

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
