from fastapi import FastAPI

app = FastAPI()

#ana dizin endpointi
@app.get("/")
def read_root():
    return 
    {
        "name" : "Task API",
        "version" : "1.0",
        "endpoints" : ["/tasks"]
    }

    
#saglık kontrolü endpointi
@app.get("/health")
def read_healt():
    return {"status" : "ok"}