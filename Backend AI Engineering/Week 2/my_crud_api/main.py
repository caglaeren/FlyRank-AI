import os
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import JSONResponse 
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import Optional
from fastapi import status
import sqlite3 #veritabanı icin
from dotenv import load_dotenv #env dosyasını okumak icin
import psycopg #python ile postgresql arasında baglantı kurmayı saglar
from psycopg.rows import dict_row #postgresql verilerini dict olarak almak icin
from supabase import create_client, Client

#.env dosyasındaki degiskenleri yüklemek icin
load_dotenv()

app = FastAPI()

header_scheme = APIKeyHeader(name="Authorization", auto_error=False)


#.envden değişkenleri alalım
DATABASE_URL = os.getenv("DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

#supabase clientini olusturalım
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)



#veritabanının baglantısını alacagız
def get_db_connection():
    # row_factory=dict_row sayesinde sütunlara sözlük gibi (t["title"]) erişebiliriz
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    return conn

#veritabanını başlatalım
#Veritabanı bağlantısı (conn) sadece veri tabanına giden bir yol açar;
#cursor ise bu yoldan yürüyerek komutları işleten işçidir
def create_db():
    conn = get_db_connection()
    cursor = conn.cursor() #veritabanında islemler yapmak icin imlec olusturur

    #Tablo oluştur (eğer yoksa) - postgresql için
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT FALSE
        )
    """)

    #Tablo boşsa ilk seferde 3 örnek ekleyelim
    cursor.execute("SELECT COUNT(*) from tasks ")
    count = cursor.fetchone()["count"] #count degerini al

    if count == 0: #ilk seferde
        ornek_tasklar = [
            ("Complete the AI projects", False),
            ("Feed the cats", True),
            ("Read a book", False)
            
        ]
        #%s işaretleri yer tutucudur (placeholder)
        cursor.executemany("Insert Into tasks (title, done) Values (%s, %s)", ornek_tasklar)
        conn.commit()
    cursor.close()
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

class AuthRequest(BaseModel):
    email: str
    password: str


#---POST AUTH ROUTES----
@app.post("/auth/signup", status_code=201, summary="Register a new user")
def signup(auth: AuthRequest):
    if not auth.email or not auth.email.strip() or not auth.password or not auth.password.strip():
        raise HTTPException(status_code=400, detail="Email and password are required.")
    try:
        response = supabase.auth.sign_up({"email": auth.email.strip(), "password": auth.password.strip()})
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/login", status_code=200, summary="Login a user")
def login(auth: AuthRequest):
    if not auth.email or not auth.email.strip() or not auth.password or not auth.password.strip():
        raise HTTPException(status_code=400, detail="Email and password are required.")
    try:
        response = supabase.auth.sign_in_with_password({"email": auth.email.strip(), "password": auth.password.strip()})
        if response.session:
            return {"access_token":response.session.access_token, "refresh_token": response.session.refresh_token}
        else:
            raise HTTPException(status_code=400, detail={"error": "Invalid login credentials."})
    except Exception as e:
        raise HTTPException(status_code=401, detail={"error":"Invalid login credentials" })


#GET ROUTES - public & protected
#Public endpoint
@app.get("/public/info", status_code=200, summary="Public info endpoint")
def public_info():
    return {"message": "Welcome stranger! This info is public."}

#Protected endpoint 
@app.get("/protected/profile", status_code=200, summary="Protected profile endpoint")
def protected_profile(authorization: Optional[str] = Depends(header_scheme)):
    #baslık hic gelmediyse hata fırlat
    if not authorization:
        return JSONResponse(status_code = status.HTTP_401_UNAUTHORIZED, content={"error": "Access token required"})
    
    #format kontrolü yapalım (Bearer ile başlayacak)
    if not authorization.strip().lower().startswith("bearer "):
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": "Access token required"})
    
    #"Bearer " kısmını ayıklayıp al ve arkasında token kalıp kalmadıgını kontrol edelim
    try:
        parts = authorization.split() 
        #eger liste 2 elemandan oluşmuyorsa bearer + token format hatalıdır
        if len(parts) != 2:
            raise IndexError
        token = parts[1]
    except IndexError:
        return JSONResponse(status_code = status.HTTP_401_UNAUTHORIZED, content={"error": "Access token required"})
    
    #sadece token sunuldugu icin basarılı don
    return {"message":"Access granted to protected route."}



#ana dizin endpointi
@app.get("/")
def read_root():
    return {
        "name" : "Task API",
        "version" : "3.0",
        "endpoints" : ["/tasks"]
    }

    
#saglık kontrolü endpointi
@app.get("/health")
def read_health():
    return {"status" : "ok"}


# --------- GET ----------

#tüm görevleri listeleyelim, okuyalım
#veritabanından okuyalım
@app.get("/tasks", summary="Get all tasks")
def read_tasks():
    conn = get_db_connection() #veritabanına baglan
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks") #veritabanından verileri al
    tasks = cursor.fetchall()
    cursor.close()
    conn.close()

    #done değerini boolean yapmak için dönüştürüyoruz
    return [{"id": t["id"], "title": t["title"], "done": bool(t["done"])} for t in tasks]

# tek bir görevi id'ye göre veritabanından getirelim
@app.get("/tasks/{task_id}", summary = "Get a task by id")
def read_task(task_id : int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("Select * from tasks where id = %s", (task_id,))
    task = cursor.fetchone() #bir tane veri gelecek
    cursor.close()
    conn.close()

    if task is None:  #veri yoksa
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")
    return {"id": task["id"], "title": task["title"], "done": bool(task["done"])}




# --------- POST ----------

#post yani yeni task ekleyelim
#201: created yani oluşturuldu isteğin başarıyla işlendiği anlamına gelir
@app.post("/tasks", status_code=201, summary="Create a new task")
def create_task(task: TaskCreate):
    #title boş ise error ver
    if not task.title or not task.title.strip():
        raise HTTPException(status_code=400, detail="Task title is required.")

    conn = get_db_connection()
    cursor = conn.cursor()

    #yeni taskı veritabanına ekleyelim, başta done 0 yani false olarak atanır default o çünkü
    cursor.execute("INSERT INTO tasks (title, done) VALUES (%s, %s) Returning id", (task.title.strip(),False))
    
    new_id = cursor.fetchone()["id"] #eklenen id yi al
    conn.commit() #post işlemini kalıcı olarak kaydetmek için

    #eklenen görevi veritabanından okuyup donelim
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (new_id,))
    created_task = cursor.fetchone()
    cursor.close()
    conn.close()

    return {"id": created_task["id"], "title": created_task["title"], "done": bool(created_task["done"])}


# --------- PUT ----------

#put : güncelleme yapalım, idye göre
#Unknown id → 404
#Empty/invalid body -> 400
@app.put("/tasks/{task_id}", status_code=status.HTTP_200_OK, summary="Update a task")
def update_task(task_id: int, task_update: TaskUpdate):
    # 1- doğrulama yapalım çünkü bir task gönderilmediyse hata fırlatsın
    if task_update.title is None and task_update.done is None:
        raise HTTPException(status_code=400, detail="At least one field must be provided. ('title' / 'done')")

    # 2- eğer title gönderildiyse boş olmadığından emin olalım
    if task_update.title is not None and not task_update.title.strip():
        raise HTTPException(status_code=400, detail="Title can not be empty.")
    
    #3- veritabanına bağlanalım
    conn = get_db_connection()
    cursor = conn.cursor()

    #4-Task veritabanında var mı bakalım
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    task = cursor.fetchone()
    if task is None: #task yoksa hata fırlat
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")

    new_title = task["title"] #taskın mevcut title'ı
    new_done = task["done"] #taskın mevcut done degeri

    # Gönderilen yeni değerler varsa güncelleyelim
    if task_update.title is not None: #title'a değer atamış mı
        new_title = task_update.title.strip()
    
    if task_update.done is not None:
        new_done = task_update.done
        

    #5-Veritabanında güncelleme yapalım
    cursor.execute("UPDATE tasks SET title = %s, done = %s WHERE id = %s", (new_title, new_done, task_id))
    conn.commit()

    #6- güncellenen veriyi çekip dönelim
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    updated_task = cursor.fetchone()
    cursor.close()
    conn.close()

    return {"id": updated_task["id"], "title": updated_task["title"], "done": bool(updated_task["done"])}

    


# --------- DELETE ----------

# delete : silme yapalım
# 204 -> no content (içerik yok) 
#204: sunucunun bir istemci isteğini başarıyla yerine getirdiğini ancak yanıt olarak herhangi bir veri veya içerik göndermediğini belirten

@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task")
def delete_task(task_id:int):
    conn = get_db_connection()
    cursor = conn.cursor()

    #Task veritabanında var mı
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    task = cursor.fetchone()
    if task is None:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")
    
    #Veritabanından silelim
    cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return #204 no content döner
