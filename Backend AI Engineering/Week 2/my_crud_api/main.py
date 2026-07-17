from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class TaskCreate(BaseModel):
    title : str


#id, title, done olacak
tasks = [
    {"id": 1, "title": "Complete the AI projects", "done": False},
    {"id": 2, "title": "Feed the cats", "done": True},
    {"id": 3, "title": "Read a book", "done": False }
    
]

#ana dizin endpointi
@app.get("/")
def read_root():
    return {
        "name" : "Task API",
        "version" : "1.0",
        "endpoints" : ["/tasks"]
    }

    
#saglık kontrolü endpointi
@app.get("/health")
def read_healt():
    return {"status" : "ok"}

#tüm görevleri listeleyelim, okuyalım
@app.get("/tasks")
def read_tasks():
    return tasks

# tek bir görevi getirelim
@app.get("/tasks/{task_id}")
def read_task(task_id : int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")


#post yani yeni task ekleyelim
#201: created yani oluşturuldu isteğin başarıyla işlendiği anlamına gelir
@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate):
    #title boş ise error ver
    if not task.title or not task.title.strip():
        raise HTTPException(status_code=400, detail="Task title is required.")

    # yeni id oluşturalım
    new_id = max([t["id"] for t in tasks]) + 1

    new_task = {
        "id" : new_id,
        "title" : task.title,
        "done" : False
    }
    tasks.append(new_task)
    return new_task


