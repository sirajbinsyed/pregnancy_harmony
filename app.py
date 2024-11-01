import re
from unicodedata import category
from flask import Flask, render_template,request,session,redirect,flash,url_for
from config import Database

app = Flask(__name__)

app.secret_key = 'your_secret_key'
# Initialize Database
db = Database()

#Guest Block

@app.route("/")
def home():
    return render_template("guest/index.html")

@app.route("/index")
def index():
    return render_template("guest/index.html")

@app.route("/logout")
def logout():
    # Clear the session data
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        # Fetch user from the database
        query = f"SELECT * FROM tbl_login WHERE username = '{username}' and password='{password}'"
        user = db.fetchone(query)

        if user:
            session['user_id'] = user['id']
            # Verify the password
            if user['type']=='admin':
                session['admin'] = user['type']
                flash("Login successful!", "success")
                return redirect(url_for('adminhome'))  
            elif user['type']=='user':
                session['user'] = user['type']
                flash("Login successful!", "success")
                return redirect(url_for('userhome'))
            else:
                flash("Invalid username or password.", "danger")
            
        else:
            flash("User not found.", "danger")

    return render_template("guest/login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Get form data
        name = request.form['name']
        address = request.form['address']
        phone = request.form['phone']
        gmail = request.form['gmail']
        age = request.form['age']
        blood = request.form['blood']
        username = request.form['username']
        password = request.form['password']
        

        try:
            # Insert into tbl_login
            insert_login_query = f"""
            INSERT INTO tbl_login (username, password, type) 
            VALUES ('{username}', '{password}', 'user')
            """
            db.single_insert(insert_login_query)

            # Retrieve the login ID
            get_login_id_query = f"SELECT id FROM tbl_login WHERE username = '{username}'"
            login_record = db.fetchone(get_login_id_query)
            login_id = login_record['id']

            # Insert into registration table
            insert_registration_query = f"""
            INSERT INTO tbl_register (login_id, name, address, phone, gmail, age, blood_group) 
            VALUES ({login_id}, '{name}', '{address}', '{phone}', '{gmail}', {age}, '{blood}')
            """
            print(insert_registration_query)
            db.single_insert(insert_registration_query)

            flash("Registration successful!", "success")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Registration failed: {str(e)}", "danger")

    return render_template("guest/register.html")


#admin Block Start-----

def checkAdmin():
    admin = session.get('admin')
    if not admin:
        return redirect(url_for('login'))

@app.route("/admin-home")
def adminhome():
    admin = checkAdmin()
    if admin:
        return admin
    
    
    fetch_count_query = f"""
        SELECT 
            SUM(CASE WHEN tbl_enquiry.status = 'initiated' THEN 1 ELSE 0 END) AS initiated_count,
            SUM(CASE WHEN tbl_enquiry.status = 'opened' THEN 1 ELSE 0 END) AS opened_count,
            SUM(CASE WHEN tbl_enquiry.status = 'closed' THEN 1 ELSE 0 END) AS closed_count
        FROM tbl_enquiry
    """

    # Execute the query to get counts
    counts = db.fetchone(fetch_count_query)
    initiated_count = int(counts['initiated_count'] or 0)
    opened_count = int(counts['opened_count'] or 0)
    closed_count = int(counts['closed_count'] or 0)
    
    print(f'counts::{opened_count}, {initiated_count},{closed_count}')
    try:
           fetch_enquiry_query = f"""
                                            SELECT 
                                                tbl_enquiry.*, 
                                                tbl_category.name AS category_name, 
                                                tbl_register.name AS user_name, 
                                                tbl_register.age AS user_age
                                            FROM tbl_enquiry
                                            LEFT JOIN tbl_category ON tbl_enquiry.cat_id = tbl_category.id
                                            LEFT JOIN tbl_register ON tbl_enquiry.user_id = tbl_register.login_id
                                            WHERE tbl_enquiry.status = 'initiated'
                                            ORDER BY tbl_enquiry.enquiry_id DESC
                                            """
           enquiries = db.fetchall(fetch_enquiry_query)
           print(f"this is the enquiries:{enquiries}")
    except Exception as e:
           flash(f"Failed to load questions: {str(e)}", "danger")

    return render_template("admin/index.html",initiated_count=initiated_count, opened_count=opened_count, closed_count=closed_count , enquiries= enquiries )

@app.route("/admin-user")
def adminuser():
    admin = checkAdmin()
    if admin:
        return admin
    users = db.fetchall("SELECT * FROM tbl_register")
    return render_template("admin/user.html", users=users)


@app.route("/admin-category", methods=["GET", "POST"])
def admincategory():
    admin = checkAdmin()
    if admin:
        return admin
    if request.method == "POST":
        category_id = request.form.get('category_id')
        category_name = request.form['category']
        details = request.form['details']

        if category_id:  # Update operation
            try:
                update_category_query = f"""
                UPDATE tbl_category 
                SET name = '{category_name}', details = '{details}'
                WHERE id = {category_id}
                """
                db.execute(update_category_query)
                flash("Category updated successfully!", "success")
            except Exception as e:
                flash(f"Failed to update category: {str(e)}", "danger")
        else:  # Create operation
            try:
                insert_category_query = f"""
                INSERT INTO tbl_category (name, details) 
                VALUES ('{category_name}', '{details}')
                """
                db.single_insert(insert_category_query)
                flash("Category added successfully!", "success")
            except Exception as e:
                flash(f"Failed to add category: {str(e)}", "danger")
        
        return redirect(url_for('admincategory'))

    # Fetch all categories and the category to edit (if any)
    categories = db.fetchall("SELECT * FROM tbl_category")
    category_to_edit = None
    if 'edit' in request.args:
        category_id = request.args.get('edit')
        category_to_edit = db.fetchone(f"SELECT * FROM tbl_category WHERE id = {category_id}")
    
    return render_template("admin/category.html", categories=categories, category_to_edit=category_to_edit)



@app.route("/delete-category/<int:category_id>", methods=["POST"])
def delete_category(category_id):
    admin = checkAdmin()
    if admin:
        return admin
    try:
        delete_query = f"DELETE FROM tbl_category WHERE id = {category_id}"
        db.execute(delete_query)
        flash("Category deleted successfully!", "success")
    except Exception as e:
        flash(f"Failed to delete category: {str(e)}", "danger")
    
    return redirect(url_for('admincategory'))



@app.route("/admin-question", methods=["GET", "POST"])
def adminquestion():
    admin = checkAdmin()
    if admin:
        return admin
    if request.method == "POST":
        question_id = request.form.get('id')
        category = request.form['question_category']
        question = request.form['question']
        upd_answer_id = request.form.getlist('upd_answer_ids[]')
        upd_answer = request.form.getlist('upd_answer[]')
        print(f"this is update answers:{upd_answer}")
        answer = request.form.getlist('answer[]')

        print(f"this is answers:{answer}")
        if question_id:  
            print(f"hello1")
            try:
                update_question_query = f"""
                UPDATE tbl_question 
                SET  category = '{category}', question = '{question}'
                WHERE question_id = {question_id}
                """
                db.execute(update_question_query)

                if upd_answer_id:
                    for answer_id, answer_text in zip(upd_answer_id, upd_answer):
                        try:
                
                            update_answer_query = f"""
                            UPDATE tbl_answer
                            SET answer = '{answer_text}'
                            WHERE id = {answer_id}
                            """
                            
                            
                            db.execute(update_answer_query)
                            
                        except Exception as e:
                            flash(f"Failed to update answer with ID {answer_id}: {str(e)}", "danger")

                if answer:
                    for ans in answer:
                        insert_answer_query = f"""
                        INSERT INTO tbl_answer (question_id, answer) 
                        VALUES ('{question_id}', '{ans}')
                        """
                    db.single_insert(insert_answer_query)
                flash("Question updated successfully!", "success")
            except Exception as e:
                flash(f"Failed to update question: {str(e)}", "danger")
        else:
            try:
                print(f"hello3")
                insert_question_query = f"""
                INSERT INTO tbl_question (category, question, created_on)
                VALUES ('{category}', '{question}', NOW())
                """
                question_id = db.executeAndReturnId(insert_question_query)
                print(f"question ID:{question_id}")
                if question_id:
                    for ans in answer:
                        insert_answer_query = f"""
                        INSERT INTO tbl_answer (question_id, answer) 
                        VALUES ('{question_id}', '{ans}')
                        """
                        db.single_insert(insert_answer_query)
                    print("added answer successfully")
                flash("Question added successfully!", "success")
            except Exception as e:
                
                flash(f"Failed to add question: {str(e)}", "danger")
                print(f"hello4{str(e)}")
        
        return redirect(url_for('adminquestion'))

    try:
        fetch_questions_query = "SELECT * FROM tbl_question"
        questions = db.fetchall(fetch_questions_query)
        fetch_category_query = "SELECT name FROM tbl_category"
        select_category = db.fetchall(fetch_category_query)
        print(f"this is the categories:{select_category}")
        question_to_edit= None
        answers_to_edit=None
        if 'edit' in request.args:
            question_id = request.args.get('edit')
            question_to_edit = db.fetchone(f"SELECT * FROM tbl_question WHERE question_id = {question_id}")
            print(question_to_edit)
            fetch_answer_query = f"SELECT * FROM tbl_answer WHERE question_id={question_id}"
            answers_to_edit = db.fetchall(fetch_answer_query)
            print(f"this is answers:{answers_to_edit}")
            
    except Exception as e:
        flash(f"Failed to load questions: {str(e)}", "danger")
        questions = []

    return render_template('admin/question.html', questions=questions ,select_category=select_category, question_to_edit=question_to_edit, answers_to_edit=answers_to_edit)


@app.route("/delete-question/<int:question_id>", methods=["POST"])
def delete_question(question_id):
    admin = checkAdmin()
    if admin:
        return admin

    try:
        print(f'question id:{question_id}')
        delete_query = f"DELETE FROM tbl_question WHERE question_id = {question_id}"
        db.execute(delete_query)
        flash("Question deleted successfully!", "success")
    except Exception as e:
        flash(f"Failed to delete question: {str(e)}", "danger")
    
    return redirect(url_for('adminquestion'))

@app.route("/delete-answer", methods=["GET", "POST"])
def delete_answer():
    admin = checkAdmin()
    if admin:
        return admin
    try:
        question_id = request.args.get('question_id')
        answer_id = request.args.get('answer_id')
        print(f'this is answer ID new:{answer_id}')
        print(f'this is question ID new:{question_id}')
        fetch_questions_query = "SELECT * FROM tbl_question"
        questions = db.fetchall(fetch_questions_query)

        fetch_category_query = "SELECT name FROM tbl_category"
        select_category = db.fetchall(fetch_category_query)
        print(f"this is the categories:{select_category}")

        print(f'answer id:{answer_id}')
        print(f'question id:{question_id}')
        delete_query = f"DELETE FROM tbl_answer WHERE id = {answer_id}"
        db.execute(delete_query)
        flash("answer deleted successfully!", "success")

       
        question_to_edit = db.fetchone(f"SELECT * FROM tbl_question WHERE question_id = {question_id}")
        print(question_to_edit)

        fetch_answer_query = f"SELECT * FROM tbl_answer WHERE question_id={question_id}"
        answers_to_edit = db.fetchall(fetch_answer_query)
        print(f"this is answers:{answers_to_edit}")

    except Exception as e:
        flash(f"Failed to delete answer: {str(e)}", "danger")
    
    return render_template('admin/question.html', questions=questions ,select_category=select_category, question_to_edit=question_to_edit, answers_to_edit=answers_to_edit)



@app.route("/admin-month-by-month", methods=["GET", "POST"])
def adminmonthbymonth():
    admin = checkAdmin()
    if admin:
        return admin
    if request.method == "POST":
        id = request.form.get('id')
        month = request.form['month']
        title = request.form['tittle']
        description = request.form['description']

       
        if id:  
            print(f"hello1")
            try:
                update_tips_query = f"""
                UPDATE tbl_month_tips
                SET  title = '{title}', description = '{description}', month='{month}', date=NOW()
                WHERE id = {id}
                """
                db.execute(update_tips_query)
                flash("tips updated successfully!", "success")
            except Exception as e:
                flash(f"Failed to update tips: {str(e)}", "danger")
        else:
            try:
                print(f"hello3")
                insert_tips_query = f"""
                INSERT INTO tbl_month_tips (title, month, description, date)
                VALUES ('{title}', '{month}', '{description}', NOW())
                """
                
                db.single_insert(insert_tips_query)
                print("added tips successfully")
               
            except Exception as e:
                
                flash(f"Failed to add question: {str(e)}", "danger")
                print(f"hello4{str(e)}")
        
        return redirect(url_for('adminmonthbymonth'))

    try:
        fetch_tips_query = "SELECT * FROM tbl_month_tips"
        tips = db.fetchall(fetch_tips_query)
       
        tips_to_edit= None
       
        if 'edit' in request.args:
            id = request.args.get('edit')
            tips_to_edit = db.fetchone(f"SELECT * FROM tbl_month_tips WHERE id = {id}")
                       
    except Exception as e:
        flash(f"Failed to load tips: {str(e)}", "danger")
    
    return render_template('admin/month_by_month.html', tips=tips, tips_to_edit=tips_to_edit)


@app.route("/delete-tip/<int:id>", methods=["POST"])
def delete_tip(id):
    admin = checkAdmin()
    if admin:
        return admin
    try:
        delete_tips_query = f"DELETE FROM tbl_month_tips WHERE id = {id}"
        db.execute(delete_tips_query)
        flash("Tip deleted successfully!", "success")
    except Exception as e:
        flash(f"Failed to delete tip: {str(e)}", "danger")
    
    return redirect(url_for('adminmonthbymonth'))

@app.route("/admin-enquiry", methods=["GET", "POST"])
def adminenquiry():
    admin = checkAdmin()
    if admin:
        return admin
    
    if 'enquiry_type' in request.args:
       enquiry_type = request.args.get('enquiry_type')
       print(f'this is enquiry type:{enquiry_type}')
       if enquiry_type == 'new_enquiry':
            try:
                    fetch_enquiry_query = f"""
                                            SELECT 
                                                tbl_enquiry.*, 
                                                tbl_category.name AS category_name, 
                                                tbl_register.name AS user_name, 
                                                tbl_register.age AS user_age
                                            FROM tbl_enquiry
                                            LEFT JOIN tbl_category ON tbl_enquiry.cat_id = tbl_category.id
                                            LEFT JOIN tbl_register ON tbl_enquiry.user_id = tbl_register.login_id
                                            WHERE tbl_enquiry.status = 'initiated'
                                            ORDER BY tbl_enquiry.enquiry_id DESC
                                            """
                    enquiries = db.fetchall(fetch_enquiry_query)
                    print(f"this is the enquiries:{enquiries}")
            except Exception as e:
                    flash(f"Failed to load questions: {str(e)}", "danger")
                    enquiries = []
            return render_template('admin/enquiry.html', enquiries=enquiries)

       else:
            try:
                    fetch_enquiry_query = f"""
                                            SELECT 
                                                tbl_enquiry.*, 
                                                tbl_category.name AS category_name, 
                                                tbl_register.name AS user_name, 
                                                tbl_register.age AS user_age
                                            FROM tbl_enquiry
                                            LEFT JOIN tbl_category ON tbl_enquiry.cat_id = tbl_category.id
                                            LEFT JOIN tbl_register ON tbl_enquiry.user_id = tbl_register.login_id
                                            WHERE tbl_enquiry.status = 'closed'
                                            ORDER BY tbl_enquiry.enquiry_id DESC
                                            """
                    enquiries = db.fetchall(fetch_enquiry_query)
                    print(f"this is the enquiries:{enquiries}")
            except Exception as e:
                    flash(f"Failed to load questions: {str(e)}", "danger")
                    enquiries = []
            return render_template('admin/enquiry.html', enquiries=enquiries)

    try:
        fetch_enquiry_query = f"""
                                SELECT 
                                    tbl_enquiry.*, 
                                    tbl_category.name AS category_name, 
                                    tbl_register.name AS user_name, 
                                    tbl_register.age AS user_age
                                FROM tbl_enquiry
                                LEFT JOIN tbl_category ON tbl_enquiry.cat_id = tbl_category.id
                                LEFT JOIN tbl_register ON tbl_enquiry.user_id = tbl_register.login_id
                                WHERE tbl_enquiry.status = 'opened'
                                ORDER BY tbl_enquiry.enquiry_id DESC
                                """
        enquiries = db.fetchall(fetch_enquiry_query)
        print(f"this is the enquiries:{enquiries}")
    except Exception as e:
        flash(f"Failed to load questions: {str(e)}", "danger")
        enquiries = []
    return render_template('admin/enquiry.html', enquiries=enquiries)


@app.route("/reply_enquiry", methods=["GET", "POST"])
def reply_enquiry():
    admin = checkAdmin()
    if admin:
        return admin
    try:
        # Handle form submission if POST request (send reply)
        if request.method == "POST":
            
            enquiry_id = request.form.get('enquiry_id')
            reply = request.form["reply"]
            type= 'admin'
            print(f'this is enquiry id 123:{enquiry_id}')

            #change status of enquiry
            update_enquiry_query = f"""
                        UPDATE tbl_enquiry 
                        SET status = 'opened'
                        WHERE enquiry_id = {enquiry_id}
                        """
            db.execute(update_enquiry_query)
            
            #insert reply with reply message
            insert_reply_query = f"""
                INSERT INTO tbl_replay (enquiry_id, reply, type, created_on)
                VALUES ({enquiry_id},'{reply}', '{type}', NOW())
            """
            db.single_insert(insert_reply_query)
            flash("reply added successfully!", "success")
            
            return redirect(url_for('reply_enquiry', enquiry_id=enquiry_id))

        enquiry_id = request.args.get('enquiry_id')
        print(f"this is enquiry ID:{enquiry_id}")
        fetch_enquiry_query =f"""
                                    SELECT 
                                        tbl_enquiry.*, 
                                        tbl_register.name AS user_name, 
                                        tbl_register.age AS user_age, 
                                        tbl_category.name AS category_name
                                    FROM tbl_enquiry
                                    LEFT JOIN tbl_register ON tbl_enquiry.user_id = tbl_register.login_id
                                    LEFT JOIN tbl_category ON tbl_enquiry.cat_id = tbl_category.id
                                    WHERE tbl_enquiry.enquiry_id = {enquiry_id}
                                """
        enquiry = db.fetchone(fetch_enquiry_query)
        print(f"this is enquiry:{enquiry}")
        # Fetch chat messages related to the enquiry
        chat_messages=None
        fetch_chat_query = f"""
                            SELECT * FROM tbl_replay WHERE enquiry_id = {enquiry_id} ORDER BY created_on ASC
                        """
        chat_messages = db.fetchall(fetch_chat_query)
        print(f"this is messages:{chat_messages}")
        

    except Exception as e:
        flash(f"Failed to load enquiry: {str(e)}", "danger")
        return redirect(url_for('enquiries'))

    return render_template('admin/chat.html', enquiry=enquiry, chat_messages=chat_messages)

@app.route("/close-enquiry", methods=["GET", "POST"])
def close_enquiry():
    admin = checkAdmin()
    if admin:
        return admin
    try:
        enquiry_id = request.args.get('enquiry_id')
        update_enquiry_query = f"""
                    UPDATE tbl_enquiry 
                    SET status = 'closed'
                    WHERE enquiry_id = {enquiry_id}
                    """
        db.execute(update_enquiry_query)
    except Exception as e:
        flash(f"Failed to close enquiry: {str(e)}", "danger")
        return redirect(url_for('enquiries'))

    return redirect(url_for('reply_enquiry', enquiry_id=enquiry_id))

#admin Block End-------

#user Block Start-----------

def checkUser():
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))

@app.route("/user-home")
def userhome():
    user = checkUser()
    if user:
        return user
    user_id = session.get('user_id')
    
    fetch_count_query = f"""
        SELECT 
            SUM(CASE WHEN tbl_enquiry.status = 'initiated' THEN 1 ELSE 0 END) AS initiated_count,
            SUM(CASE WHEN tbl_enquiry.status = 'opened' THEN 1 ELSE 0 END) AS opened_count,
            SUM(CASE WHEN tbl_enquiry.status = 'closed' THEN 1 ELSE 0 END) AS closed_count
        FROM tbl_enquiry
        WHERE tbl_enquiry.user_id = {user_id}
    """

    # Execute the query to get counts
    counts = db.fetchone(fetch_count_query)

    initiated_count = int(counts['initiated_count'] or 0)
    opened_count = int(counts['opened_count'] or 0)
    closed_count = int(counts['closed_count'] or 0)
    enquiries= None
    try:
        fetch_enquiry_query = f"""
            SELECT tbl_enquiry.*, tbl_category.name AS category_name 
            FROM tbl_enquiry 
            LEFT JOIN tbl_category ON tbl_enquiry.cat_id = tbl_category.id 
            WHERE tbl_enquiry.user_id = {user_id} 
            AND (tbl_enquiry.status = 'opened' OR tbl_enquiry.status = 'replied') 
            ORDER BY tbl_enquiry.enquiry_id DESC
            """
        enquiries = db.fetchall(fetch_enquiry_query)
        print(f"this is the enquiries:{enquiries}")
    except Exception as e:
        flash(f"Failed to load questions: {str(e)}", "danger")
        print(f"this is the enquiries:{e}")

    print(f'counts::{opened_count}, {initiated_count},{closed_count}')
   
    return render_template("user/index.html", initiated_count=initiated_count, opened_count=opened_count, closed_count=closed_count, enquiries= enquiries)
    
@app.route("/user-enquiry", methods=["GET", "POST"])
def userenquiry():
    user = checkUser()
    if user:
        return user
    fetch_category_query = "SELECT id,name FROM tbl_category"
    select_category = db.fetchall(fetch_category_query)
    print(f"this is the categories:{select_category}")
    user_id = session.get('user_id')
   
    if request.method == "POST":
        
        category_id = request.form['category_id']
        subject = request.form['subject']
        enquiry = request.form['enquiry']
        
        print(f"this is user Id :{user_id}")
        try:
                insert_enquiry_query = f"""
                INSERT INTO tbl_enquiry (user_id, cat_id, subject, enquiry, status) 
                VALUES ('{user_id}', '{category_id}', '{subject}', '{enquiry}', 'initiated')
                """
                db.single_insert(insert_enquiry_query)
                flash("Enquiry added successfully!", "success")
        except Exception as e:
                flash(f"Failed to add enquiry: {str(e)}", "danger")
        
        return redirect(url_for('userenquiry'))

    try:
        fetch_enquiry_query = f"""
        SELECT tbl_enquiry.*, tbl_category.name as category_name 
        FROM tbl_enquiry 
        LEFT JOIN tbl_category ON tbl_enquiry.cat_id = tbl_category.id 
        WHERE tbl_enquiry.user_id = {user_id}  AND tbl_enquiry.status = 'initiated'
        """
        enquiries = db.fetchall(fetch_enquiry_query)
        print(f"this is the enquiries:{enquiries}")
    except Exception as e:
        flash(f"Failed to load questions: {str(e)}", "danger")
        enquiries = []
    return render_template('user/enquiry.html', enquiries=enquiries, select_category=select_category)

@app.route("/user-opened-enquiry", methods=["GET", "POST"])
def user_opened_enquiry():
    status = request.args.get('status')
    print(f'this is status :{status}')
    user = checkUser()
    if user:
        return user
    fetch_category_query = "SELECT id,name FROM tbl_category"
    select_category = db.fetchall(fetch_category_query)
    print(f"this is the categories:{select_category}")
    user_id = session.get('user_id')

    try:
        
        fetch_enquiry_query = f"""
            SELECT tbl_enquiry.*, tbl_category.name as category_name 
            FROM tbl_enquiry 
            LEFT JOIN tbl_category ON tbl_enquiry.cat_id = tbl_category.id 
            WHERE tbl_enquiry.user_id = {user_id}  AND tbl_enquiry.status = '{status}'
            """   
        enquiries = db.fetchall(fetch_enquiry_query)
        print(f"this is the enquiries:{enquiries}")
    except Exception as e:
        flash(f"Failed to load questions: {str(e)}", "danger")
        enquiries = []
    return render_template('user/check_enquiry.html', enquiries=enquiries, select_category=select_category)




@app.route("/user_reply", methods=["GET", "POST"])
def user_reply():
    user = checkUser()
    if user:
        return user
    user_id = session.get('user_id')
    try:
        # Handle form submission if POST request (send reply)
        if request.method == "POST":
            
            enquiry_id = request.form.get('enquiry_id')
            reply = request.form["reply"]
            type= 'user'
            print(f'this is enquiry id 123:{enquiry_id}')
            insert_reply_query = f"""
                INSERT INTO tbl_replay (enquiry_id, reply, type, created_on)
                VALUES ({enquiry_id},'{reply}', '{type}', NOW())
            """
            db.single_insert(insert_reply_query)
            flash("reply added successfully!", "success")
            
            return redirect(url_for('user_reply', enquiry_id=enquiry_id))

        enquiry_id = request.args.get('enquiry_id')
        print(f"this is enquiry ID:{enquiry_id}")
        fetch_enquiry_query =f"""
                                    SELECT 
                                        tbl_enquiry.*, 
                                        tbl_register.name AS user_name, 
                                        tbl_register.age AS user_age, 
                                        tbl_category.name AS category_name
                                    FROM tbl_enquiry
                                    LEFT JOIN tbl_register ON tbl_enquiry.user_id = tbl_register.login_id
                                    LEFT JOIN tbl_category ON tbl_enquiry.cat_id = tbl_category.id
                                    WHERE tbl_enquiry.enquiry_id = {enquiry_id}
                                """
        enquiry = db.fetchone(fetch_enquiry_query)
        print(f"this is enquiry:{enquiry}")
        # Fetch chat messages related to the enquiry
        chat_messages=None
        fetch_chat_query = f"""
                            SELECT * FROM tbl_replay WHERE enquiry_id = {enquiry_id} ORDER BY created_on ASC
                        """
        chat_messages = db.fetchall(fetch_chat_query)
        print(f"this is messages:{chat_messages}")
        

    except Exception as e:
        flash(f"Failed to load enquiry: {str(e)}", "danger")
        return redirect(url_for('enquiries'))

    return render_template('user/chat.html', enquiry=enquiry, chat_messages=chat_messages)

@app.route("/user_FAQ", methods=["GET"])
def user_faq():
    user = checkUser()
    if user:
        return user
   
    fetch_category_query = f"""
                            SELECT * FROM tbl_category
                        """
    category_details = db.fetchall(fetch_category_query)
    print(f"this is messages:{category_details}")
    return render_template("user/FAQ.html", categories=category_details)

@app.route("/user_FAQ_category", methods=["GET", "POST"])
def user_faq_category():
    user = checkUser()
    if user:
        return user
    category_name= request.args.get('category_name')
    date = request.args.get('date')
    print(f"this is date:{date}")
    if date:
          
            month_year = date.split("-")  
            year = month_year[0]  
            month = month_year[1] 
            start_date = f"{year}-{month}-01 00:00:00"  # Start of the month
            end_date = f"{year}-{month}-31 23:59:59"  # End of the month (assuming 31 days)
            fetch_faq_query = f"""
                SELECT question_id, question, 
                    DATE_FORMAT(created_on, '%b') AS month,  -- Abbreviated month name (Jan, Feb, etc.)
                    DATE_FORMAT(created_on, '%Y') AS year    -- Four-digit year
                FROM tbl_question
                WHERE category = '{category_name}'
                AND created_on BETWEEN '{start_date}' AND '{end_date}'
                ORDER BY created_on DESC
                    """
            faq_details = db.fetchall(fetch_faq_query)
            print(f"this is questions: {faq_details}")

            # Fetch answers for the filtered questions
            fetch_answers_query = f"""
                SELECT question_id, id AS answer_id, answer AS answer
                FROM tbl_answer
                WHERE question_id IN (
                    SELECT question_id
                    FROM tbl_question
                    WHERE category = '{category_name}'
                    AND created_on BETWEEN '{start_date}' AND '{end_date}'
                )
            """
            answers = db.fetchall(fetch_answers_query)
            print(f"this is answers: {answers}")
    else:
            fetch_faq_query = f"""
                        SELECT question_id, question, 
                            DATE_FORMAT(created_on, '%b') AS month,  -- Abbreviated month name (Jan, Feb, etc.)
                            DATE_FORMAT(created_on, '%Y') AS year    -- Four-digit year
                        FROM tbl_question
                        WHERE category = '{category_name}'
                        ORDER BY created_on DESC
                    """
            faq_details = db.fetchall(fetch_faq_query)
            print(f"this is questions:{faq_details}")

            fetch_answers_query = f"""
                SELECT question_id, id AS answer_id, answer AS answer
                FROM tbl_answer
                WHERE question_id IN (
                    SELECT question_id
                    FROM tbl_question 
                    WHERE category = '{category_name}'
                )
            """
            answers = db.fetchall(fetch_answers_query)
            print(f"this is answers:{answers}")

    return render_template("user/FAQ_category.html", faq_details=faq_details, answers=answers, category_name=category_name )

@app.route("/user_month_tips", methods=["GET"])
def user_month_tips():
    user = checkUser()
    if user:
        return user
   
    return render_template("user/month.html")

@app.route("/user_month_by_month", methods=["GET", "POST"])
def user_month_by_month():
    user = checkUser()
    if user:
        return user
    month= request.args.get('month')
    # date = request.args.get('date')
    # print(f"this is date:{date}")
    # if date:
          
    #         month_year = date.split("-")  
    #         year = month_year[0]  
    #         month = month_year[1] 
    #         start_date = f"{year}-{month}-01 00:00:00"  # Start of the month
    #         end_date = f"{year}-{month}-31 23:59:59"  # End of the month (assuming 31 days)
    #         print(f"start date:{start_date}, end data:{end_date},month:{month}")
    #         fetch_tips_query = f"""
    #             SELECT  title, description,
    #                 DATE_FORMAT(date, '%d-%m-%Y') AS date
    #             FROM tbl_month_tips
    #             WHERE month = '{month}'
    #             AND date BETWEEN '{start_date}' AND '{end_date}'
    #             ORDER BY date DESC
    #                 """
    #         tips = db.fetchall(fetch_tips_query)
    #         print(f"this is questions: {tips}")

           
    # else:
    fetch_tips_query = f"""
                        SELECT title, description,
                            DATE_FORMAT(date, '%d-%m-%Y') AS date
                        FROM tbl_month_tips
                        WHERE month = '{month}'
                        ORDER BY date DESC
                    """
    tips = db.fetchall(fetch_tips_query)
    print(f"this is questions:{tips}")
     
    return render_template("user/month_by_month.html", tips=tips)

#User Block End --------

#Guest Block Start -----

@app.route("/FAQ", methods=["GET"])
def faq():
   
    fetch_category_query = f"""
                            SELECT * FROM tbl_category
                        """
    category_details = db.fetchall(fetch_category_query)
    print(f"this is messages:{category_details}")
    return render_template("guest/FAQ.html", categories=category_details)

@app.route("/FAQ_category", methods=["GET", "POST"])
def faq_category():
    category_name= request.args.get('category_name')
    date = request.args.get('date')
    print(f"this is date:{date}")
    if date:
          
            month_year = date.split("-")  
            year = month_year[0]  
            month = month_year[1] 
            start_date = f"{year}-{month}-01 00:00:00"  # Start of the month
            end_date = f"{year}-{month}-31 23:59:59"  # End of the month (assuming 31 days)
            fetch_faq_query = f"""
                SELECT question_id, question, 
                    DATE_FORMAT(created_on, '%b') AS month,  -- Abbreviated month name (Jan, Feb, etc.)
                    DATE_FORMAT(created_on, '%Y') AS year    -- Four-digit year
                FROM tbl_question
                WHERE category = '{category_name}'
                AND created_on BETWEEN '{start_date}' AND '{end_date}'
                ORDER BY created_on DESC
                    """
            faq_details = db.fetchall(fetch_faq_query)
            print(f"this is questions: {faq_details}")

            # Fetch answers for the filtered questions
            fetch_answers_query = f"""
                SELECT question_id, id AS answer_id, answer AS answer
                FROM tbl_answer
                WHERE question_id IN (
                    SELECT question_id
                    FROM tbl_question
                    WHERE category = '{category_name}'
                    AND created_on BETWEEN '{start_date}' AND '{end_date}'
                )
            """
            answers = db.fetchall(fetch_answers_query)
            print(f"this is answers: {answers}")

    else:
            fetch_faq_query = f"""
                        SELECT question_id, question, 
                            DATE_FORMAT(created_on, '%b') AS month,  -- Abbreviated month name (Jan, Feb, etc.)
                            DATE_FORMAT(created_on, '%Y') AS year    -- Four-digit year
                        FROM tbl_question
                        WHERE category = '{category_name}'
                        ORDER BY created_on DESC
                    """
            faq_details = db.fetchall(fetch_faq_query)
            print(f"this is questions:{faq_details}")

            fetch_answers_query = f"""
                SELECT question_id, id AS answer_id, answer AS answer
                FROM tbl_answer
                WHERE question_id IN (
                    SELECT question_id
                    FROM tbl_question 
                    WHERE category = '{category_name}'
                )
            """
            answers = db.fetchall(fetch_answers_query)
            print(f"this is answers:{answers}")
    
    return render_template("guest/FAQ_category.html", faq_details=faq_details, answers=answers, category_name=category_name )

#Guest Block End------

# running application 
if __name__ == '__main__': 
    app.run(debug=True) 