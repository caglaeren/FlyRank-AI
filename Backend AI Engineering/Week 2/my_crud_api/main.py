from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from fastapi import status
import sqlite3 #veritabanı icin


app = FastAPI()


#veritabanını olustuyoruz
DB_NAME = "tasks.db"

#veritabanını başlatalım
def create_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    #Tablo oluştur (eğer yoksa)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT 0
        )
    """)

    #Tablo boşsa ilk seferde 3 örnek ekleyelim
    cursor.execute("SELECT COUNT(*) from tasks ")
    count = cursor.fetchone()[0] #ilk satır ilk sutun

    if count == 0: #ilk seferde
        ornek_tasklar = [
            ("Complete the AI projects", 0),
            ("Feed the cats", 1),
            ("Read a book", 0)
            
        ]
        cursor.executemany("Insert Into tasks (title, done) Values (?, ?)", ornek_tasklar)
        conn.commit()
    conn.close()

#Uygulama ayağa kalkarken veritabanını hazırlayalım
@app.on_event("startup")
async def startup_event():
    create_db()

#pydantic modelleri
class TaskCreate(BaseModel):
    title : str

class TaskUpdate(BaseModel):
    title : Optional[str] = None
    done: Optional[bool] = None

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
        "version" : "2.0",
        "endpoints" : ["/tasks"]
    }

    
#saglık kontrolü endpointi
@app.get("/health")
def read_healt():
    return {"status" : "ok"}

#tüm görevleri listeleyelim, okuyalım
@app.get("/tasks", summary="Get all tasks")
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
@app.post("/tasks", status_code=201, summary="Create a new task")
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


#put : güncelleme yapalım, idye göre
#Unknown id → 404
#Empty/invalid body -> 400
@app.put("/tasks/{task_id}", status_code=status.HTTP_200_OK, summary="Update a task")
def update_task(task_id: int, task_update: TaskUpdate):
    # 1- taskı bulalım
    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break
    
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")

    # 2- doğrulama yapalım
    if task_update.title is None and task_update.done is None:
        raise HTTPException(status_code=400, detail="At least one field must be provided. ('title' / 'done')")
    
    # 3- güncelleme - update
    if task_update.title is not None:
        if not task_update.title.strip():
            raise HTTPException(status_code=400, detail="Title can not be empty.")
        task["title"] = task_update.title.strip()
    if task_update.done is not None:
        task["done"] = task_update.done

    return task



# delete : silme yapalım
# 204 -> no content (içerik yok) 
#204: sunucunun bir istemci isteğini başarıyla yerine getirdiğini ancak yanıt olarak herhangi bir veri veya içerik göndermediğini belirten

@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task")
def delete_task(task_id:int):
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            tasks.pop(i)
            return
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")