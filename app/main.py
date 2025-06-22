from fastapi import FastAPI,Header
from app.Database.session import get_db,engine
from contextlib import asynccontextmanager
from app.books.routers import  book_router
from app.Database .async_verification_routers import verification_router
from .auth.routers import user_router



"""
In FastAPI, the lifespan is used to define startup and shutdown events — things you want to initialize once when the app starts, and clean up once when it stops.

✅ Why use lifespan?
You use it to:

🔹 1. Initialize global resources
For example:

Create database connections

Connect to Redis, Kafka, RabbitMQ, etc.

Start background tasks or schedulers

Load configuration or machine learning models
"""

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("Starting up...")
    yield
    # Shutdown
    print("Shutting down...")
    await engine.dispose()


# Create FastAPI app with lifespan
app = FastAPI(
    title="Book Management API",
    description="Async FastAPI with SQLAlchemy and Alembic",
    version="1.0.0",
    lifespan=lifespan
)


app.include_router(book_router)
app.include_router(verification_router)
app.include_router(user_router)



@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Book Management API is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )





















@app.get('/')
async def read_root():
    return {"Message":"Hello world"}


#path parameter
# http://127.0.0.1:8000/greet/sakib
@app.get('/greet/{name}')
async def greet_name(name:str)->dict:
    return {"message":f"Hello {name}"}


# quey parameter
#http://127.0.0.1:8000/greets?name=sakib
@app.get('/greets')
async def greet_name(name:str)->dict:
    return {"message":f"Hello {name}"}



#both 
# http://127.0.0.1:8000/greetss/sakib?age=26&gender=Male
from typing import Optional

@app.get('/greetss/{name}')
async def greet_name(name:str,age:int,gender:Optional[str]="others")->dict:
    return {"message":f"Hello {name} and age is {age} and its gender is {gender}"}


from pydantic import BaseModel

class BookCreateSchema(BaseModel):
    title:str
    author:str


@app.post("/create_book")
async def create_book(bookData:BookCreateSchema):
    return {
        "title":bookData.title,
        "author":bookData.author
    }




@app.get('/getHeader',status_code=200)
async def get_header(
    accept:str=Header(None),
    content_type:str = Header(None), 
    user_agent:str=Header(None),
    host:str=Header(None)
):
    request_header={}
    request_header["Accept"]=accept
    request_header["Content-Type"]=content_type
    request_header["User-Agent"]=user_agent
    request_header["Host"]=host
    return request_header 




import time
import asyncio
import threading

@app.get("/sync")
def sync_sleep():
    time.sleep(10)  # blocks the entire process
    print(f"Current thread: {threading.current_thread().name}")
    return {"message": "Synchronous response after 5 seconds"}

@app.get("/sync3")
def getUSer_data():
    print(f"Current thread: {threading.current_thread().name}")
    return {"message": "fetch data successfully"}

@app.get("/async")
async def async_sleep():
    await asyncio.sleep(5)  # non-blocking sleep
    return {"message": "Asynchronous response after 5 seconds"}