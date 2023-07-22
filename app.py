from flask import Flask, jsonify, request
from flask_cors import CORS

from database import DataBase
from task import Task
from run import start_scraper

from multiprocessing import Pool
import json
import pandas as pd
import os


app = Flask(__name__)
CORS(app)

web_app_url = os.environ.get('WEB_APP_URL')
app.config["CORS_ORIGINS"] = []


db = DataBase()


@app.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Welcome to the API"}), 200


@app.route('/task/', methods=['POST'])
def create_task():
    session_id = request.json.get('sessionId')
    if not session_id:
        return jsonify({"error": "Session ID not found"}), 404

    db.delete_task(session_id)
    key = db.create_task(session_id)

    pool = Pool(1)
    pool.apply_async(start_scraper, args=(session_id,))

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

    score_data = task.course_score
    score_data = [i.to_dict() for i in score_data]
    if not score_data:
        return jsonify({
            "status": "ERROR",
            "error": "An unknown error occurred.",
            "message": "Please resubmit Session ID",
            "taskCompleted": False
        }), 200

    response = prepare_response(task)

    return jsonify({
        "status": task.status,
        "data": response,
        "message": "Task completed successfully",
        "taskCompleted": True
    }), 200


def prepare_response(task):
    profile_data = task.student_profile.to_dict()
    score_data = task.course_score
    score_data = [i.to_dict() for i in score_data]
    # sorting by class time
    attendace_data = sorted(task.attendance, key=lambda x: x.start_time)
    attendance_data = [i.to_dict() for i in attendace_data]

    attendance_df = pd.DataFrame(attendance_data)
    
    course_score_df = pd.DataFrame(score_data)
    to_int_cols = ["marks", "total_marks"]
    for col in to_int_cols:
        course_score_df[col] = course_score_df[col].apply(float)
    course_ids = course_score_df["course_id"].unique().tolist()

    response = {
        "profileData": profile_data,
        "courseIds": course_ids,
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

    for course_id, course_df in course_score_df.groupby("course_id"):
        attendance_obj = {"attendanceData": []}
        if course_id not in response["coursesData"]:
            response["coursesData"][course_id] = {
                "courseScore": {},
            }

        course_attendance_df = attendance_df[attendance_df["course_id"] == course_id]
        attendance_obj['overview'] = {
            "total": course_attendance_df.shape[0],
            "present": course_attendance_df[course_attendance_df['attended'] == True].shape[0],
            "absent": course_attendance_df[course_attendance_df['attended'] == False].shape[0],
        }
        for attendance_type, attendance_type_df in course_attendance_df.groupby("attendance_type"):
            attendance_obj["attendanceData"].append({
                "attendanceType": attendance_type,
                "attendance": attendance_type_df.shape[0],
                "total": attendance_type_df.shape[0],
                "present": attendance_type_df[attendance_type_df['attended'] == True].shape[0],
                "absent": attendance_type_df[attendance_type_df['attended'] == False].shape[0],
                "attendance": attendance_type_df.to_dict(orient="records")
            })

        response["coursesData"][course_id]["attendance"] = attendance_obj

        for section_title, section_df in course_df.groupby('section_title'):
            total_marks = section_df["total_marks"].sum()
            marks = section_df["marks"].sum()
            percentage = round(((marks / total_marks) * 100), 2)
            section_data = section_df.to_dict(orient="records")
            response["coursesData"][course_id]['courseScore'][section_title] = {
                "totalMarks": total_marks,
                "marks": marks,
                "percentage": percentage,
                "data": section_data
            }

    return response


os.mkdir("Logs") if not os.path.exists("Logs") else None

if __name__ == '__main__':
    app.run()
