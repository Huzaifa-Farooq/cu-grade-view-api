from flask import Flask, jsonify, request
from flask_cors import CORS

from database import DataBase
from task import Task
from scraper.run_scraper import run_scraper

from multiprocessing import Pool
import json
import pandas as pd
import os


app = Flask(__name__)
CORS(app)
db = DataBase()


@app.route('/index', methods=['GET'])
def index():
    return jsonify({"message": "Welcome to the API"}), 200


@app.route('/task/', methods=['POST'])
def create_task():
    session_id = request.json.get('sessionId')
    if not session_id:
        return jsonify({"error": "Session ID not found"}), 404

    db.clean_task_data(session_id)
    db.delete_task(session_id)
    key = db.create_task(session_id)

    pool = Pool(1)
    pool.apply_async(run_scraper, args=(session_id,))

    db.update_task_status(session_id, Task.STARTED)

    return jsonify({'task_id': session_id, "key": key}), 202


@app.route('/task/<task_id>', methods=['GET'])
def get_task_status(task_id):
    # task = long_running_task.AsyncResult(task_id)
    response = {'status': task.status}
    if task.status == 'SUCCESS':
        response['result'] = task.result
    return jsonify(response)

@app.route("/taskdata/<task_id>", methods=["GET"])
def get_task_data(task_id):
    task = db.get_task(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    # getting key from request
    key = request.args.get("key", type=str)
    if not key:
        return jsonify({"error": "Key not found"}), 404
    
    # checking if key is valid
    if key != task.key:
        return jsonify({"error": "Invalid key"}), 403

    if task.status in [Task.STARTED, Task.IN_PROGRESS, Task.PENDING]:
        return jsonify({
            "status": task.status,
            "message": "Task is in progress",
            }), 200

    if task.status == Task.FAILED:
        return jsonify({
            "error": "Task failed.",
            "status": task.status,
            "message": task.message
            }), 200

    profile_data = db.get_student_profile_data(task_id)
    data = db.get_task_course_score_data(task_id)
    data = [i.to_dict() for i in data]
    
    df = pd.DataFrame(data)
    to_int_cols = ["marks", "total_marks"]
    for col in to_int_cols:
        df[col] = df[col].apply(float)

    response = {
        "profileData": profile_data,
        "courseIds": df["course_id"].unique().tolist(),
        "columns": ["section_title", "title", "marks", "total_marks", "datetime"],
        "courseInfoColumns": ["course_id", "course_name", "credit_hours", "teacher"],
        "columnsTitles": {
            "course_id": "Course ID",
            "course_name": "Course Name",
            "credit_hours": "Credit Hours",
            "teacher": "Teacher",
            "section_title": "Section",
            "title": "Title",
            "marks": "Marks",
            "total_marks": "Total Marks",
            "datetime": "Date"
        },
        "coursesData": {}
    }

    for course_id, course_df in df.groupby("course_id"):
        if course_id not in response["coursesData"]:
            response["coursesData"][course_id] = {}

        for section_title, section_df in course_df.groupby('section_title'):
            total_marks = section_df["total_marks"].sum()
            marks = section_df["marks"].sum()
            percentage = round(((marks / total_marks) * 100), 2)
            section_data = section_df.to_dict(orient="records")
            response["coursesData"][course_id][section_title] = {
                "totalMarks": total_marks,
                "marks": marks,
                "percentage": percentage,
                "data": section_data
            }

    return jsonify({
        "status": task.status,
        "data": response,
        "message": "Task completed successfully",
        "taskCompleted": True
    }), 200


os.mkdir("Logs") if not os.path.exists("Logs") else None

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2000, debug=True)
