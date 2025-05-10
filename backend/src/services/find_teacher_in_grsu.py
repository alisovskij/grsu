import requests
from fastapi import HTTPException


def find_teacher_in_grsu(email: str):
    try:
        response = requests.get(
            'http://api.grsu.by/1.x/app2/getTeachers?extended=true'
        )
        teachers = response.json()["items"]
        return next((t for t in teachers if t.get('email') == email), None)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
