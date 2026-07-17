from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {
        "status": "Ok",
         "message" : "Backend server is running!"
    }


@app.get("/api/v1/info")
def info():
    return {
        "track" : "Backend AI Engineering",
         "week" : 1,
          "assignment" : "First Api Endpoint" 
    }
