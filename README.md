# True Colors Web Application
An online/web version of the _[True Colors](https://www.truecolorsintl.com/about)_ personality assessment typically completed using pencil and paper in _CSCI 243.2: Preparing For A Computing Career_.

Final project designed for _CSCI 298/398: Web Programming_.

### Contributers
- [Jack Drabic](https://github.com/JackJack7890)
- [Rafael Garcia Jr.](https://github.com/RGJ-713)
- [Michael Romero](https://github.com/MichaelRomero1)

### Prerequisites:

- MySQL | ([Download](https://dev.mysql.com/downloads/mysql/), [Set-Up Tutorial](https://dev.mysql.com/doc/mysql-getting-started/en/))

# Installation

### 1. Clone the repository

Once you are all set up, press the green `<> Code` button to gain a link to clone the repository.

Then, open your preferred [IDE](https://aws.amazon.com/what-is/ide/) and clone the repository.

### 2. Install 'requirements.txt' file

Once the repo has been cloned through your preferred IDE, run the following commands in your IDE's terminal:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Create a .env file

Within the IDE, create a file in the project simply called `.env` and create a line that has `FLASK_SECRET_KEY =""`.

Next, go into the terminal and run the following commands:

```
python3
import secrets
print(secrets.token_hex())
```

A string of text should have been generated after the `print` command was used. Copy and paste the generated value in-between the `""` quotes in the `.env` file.

After this, also create three new lines in the .env file as follows:
```
MYSQL_HOST=""
MYSQL_USER=""
MYSQL_PASSWORD=""
```

The MYSQL_HOST will be localhost if running locally, or the IP address on Ec2
The MYSQL_USER and MYSQL_PASSWORD are whatever username and password you are using for the database

### 4. Creating the 'test_db' database

Open up the [Terminal](https://support.apple.com/guide/terminal/welcome/mac) and log in to your MySQL account.

Once you've logged in, run the following command:

```
CREATE DATABASE test_db;
```

Next, open the [Finder](https://support.apple.com/guide/mac-help/organize-your-files-in-the-finder-mchlp2605/mac) and locate the folder called `trueColorsWebApp`.

Open the folder, right-click the subfolder called `database`, and select the `New Terminal at Folder` option.

In the newly opened Terminal, run the following command (be sure to replace `YOUR_NAME` with the name of your MySQL user account):

```
mysql -u YOUR_NAME -p test_db < create.sql
```

You will then be prompted to enter your password.

After doing this, run the following command, once again replacing `YOUR_NAME` with the name of your MySQL user account:

```
mysql -u YOUR_NAME -p test_db < insert.sql
```

You will once again be prompted to enter your password.

At this point, the database should have successfully been populated.

In order to ensure this, it is suggested to go back into the Terminal that the database was created in and run the following commands:

```
USE test_db;
SHOW TABLES;
SELECT * FROM q_group_1;
```

If 6 tables are listed and `q_group_1` contains 1 row of information, the database was successfully populated.

### 5. Connecting to the MySQL database

Go back into the IDE with the opened project. Go to the `server.py` file.

Go to `Line 103` in the file and locate the following code:

```
cnx = mysql.connector.connect(user='project', password='project',
```

Replace the first `project` with the name of your MySQL user account, and replace the second `project` with the password to that account.

This will allow the project to connect to your MySQL database in order to load each question of the personality test, as well as store user results in the `user_colors` table of the database.

### 6. Running the project

You are now ready to launch the project locally.

In your IDE, run the `server.py` file.

Once the server is running, open a new tab. In your browser's search bar, type in `localhost:8000` and hit `enter`.

The True Colors Personality Test should successfully be running. As you progress through the test, each set of questions should be loading in, as well.

**It is important to note that the project will be running on a development server. This should NOT be the case in a production deployment.**

# Creating an EC2 instance

In AWS EC2, click `Create Instance`.

-- Select Name as: TrueColorsWebApp

-- Select Image as: AMI: Amazon Linux 2 AMI (HVM)

-- Select Instance Type as: `t2.micro`

-- Select Key Pair (Login) as: `vockey`

-- Network Settings: Allow SSH traffic from anywhere, Allow HTTP traffic from the internet

-- Click `Create Instance`

In a new Terminal window, run the following commands (replacing anything with `<>` characters and excluding those characters):

```
ssh -i ~/.ssh/labsuser.pem ec2-user@<YOUR IPv4 ADDRESS OR DNS>
sudo yum install -y git
git clone <YOUR_REPO>
cd trueColorsWebApp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Now, open a new Terminal window (do not delete the old one) and run the following commands:

```
sudo amazon-linux-extras install mariadb10.5
sudo systemctl start mariadb
sudo mysql_secure_installation
```

After running this command, it will prompt you to hit `return` if you do not already have a previous password. Simply hit `return`.

After that, you will be asked a series of Y/N questions. For the first one, enter `N`.

For the rest, enter `Y`. You will be prompted after the first `Y` to create a password and confirm the password.

Once a password has been created, run the following command (replacing `YOUR_NAME` with the name of your MySQL user account):
    
```
mariadb -u YOUR_NAME -p
```

You will be prompted to enter your password. This is the same password you created in the previous step. Enter the password and hit `return`.
 
Run the `create.sql` and `insert.sql` commands from the previous step, as well.
 
Once you finish running these commands, go back to the previous Terminal window where you cloned the GitHub repo and enter the following:

```
sudo /home/ec2-user/trueColorsWebApp/.venv/bin/gunicorn -w4 --bind 0.0.0.0:80 --chdir /home/ec2-user/trueColorsWebApp "server:create_app()"
```

If successful, you should be able to enter the IP address of the EC2 instance in your browser's search bar and access the functioning True Colors personality test.

In order to make the database work in the webapps box I had to use this command
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'your_password';
FLUSH PRIVILEGES;


### Steps to login into TrueColors
- Clone the respository from github https://github.com/MoravianUniversity/trueColorsWebApp
- cd into the respository after it has been cloned
- Install the requirements.txt file into a virtual environment. This can be done using the following commands
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
- Create the database. To do this, log into mysql and create the database TrueColors, using the following commands
```
mysql -u YOUR_USERNAME -p
CREATE DATABASE TrueColors;
exit
```
This creates the database, and after that is done, use the following commands to populate the database
```
mysql -u YOUR_USERNAME -p TrueColors < database/create.sql 
mysql -u YOUR_USERNAME -p TrueColors < database/insert.sql
```
This will prompt you for your mysql password.

- Finally, you must create a .env file which is individual to you. The .env file must look like this:
```
GOOGLE_CLIENT_ID="YOUR_GOOGLE_CLIENT_ID"
FLASK_SECRET_KEY="YOUR_FLASK_SECRET_KEY"
MYSQL_HOST="localhost"
MYSQL_USER="YOUR_USERNAME"
MYSQL_PASSWORD="YOUR_PASSWORD"
MYSQL_DATABASE="TrueColors"
GOOGLE_CLIENT_SECRET="YOUR_GOOGLE_CLIENT_SECRET
```
In order to get a secure FLASK_SECRET_KEY, you can use python secrets. In order to do this, in your terminal, perform the following commands
```
python3
import secrets
print(secrets.token_hex())
```
This will print a long string of numbers and letters. Copy this, and make this the value for the FLASK_SECRET_KEY

Replace MYSQL_USERNAME and MYSQL_PASSWORD with your appropriate mysql username and password respectively.

In order to get a GOOGLE_CLIENT_ID and a GOOGLE_CLIENT_SECRET, you must get them from the google console api website. 
To do this, go to the following website:

https://console.cloud.google.com

Agree to the terms of services, and then in the top left, click "Select A Project"
There will be an option in the pop-up box to create a new project. Select that to create a new project
Give your project a name (for example, TrueColors) and for the organization and location, make sure it is moravian.edu so only moravian students can access the quiz.

Now you can go back to the "Select A Project" option and select your newly created project.
Afterwards, on the left, select APIs and Services, and select under that, OAuth Consent Screen.

For the usertype, click internal and then create. Give the app a name, and for the support email and developer contact email, you may use your own email.
Now at the bottom you can click save and continue, and on the next screen also click save and continue at the bottom and click "go back to dashboard"

After this, on the leftside under APIs and Services, click credentials. 
Now click + create credentials, and select OAuth Client ID
In the dropdown, select Web Application. Give the application a name and where it says Authorized Redirect URIs, include the following three Redirect URI's:

http://127.0.0.1:8000/login
http://127.0.0.1:8000/authorize
http://localhost:8000/authorize

After this, click create.

A pop-up will appear showing your google client id, and your google client secret. These are the respective GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET values that you should put in your .env file!

If you need to grab them again at any time, you may click your application name in credentials under APIs and Services and they will be displayed on the right.

- Run server.py with ```python3 server.py``` and all should be well!


Please note, that in order for a student to sign into the student sign in for the quiz, they must have a valid moravian.edu domain email.

Please note, that in order for someone to sign into the faculty page, their email must be in the allowed_faculty_emails list in server.py on line 95
