from typing import Annotated
from fastapi import FastAPI, Query, Depends, Header, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field


app=FastAPI()
author="anonymous"

class Note(BaseModel):
    note_title:str=Field(..., description="The title of the note")
    note:str=Field(..., description="The note")
    Author:str=Field(default=author, description="The Author of the note")

class noteId(Note):
    noteId:int=Field(..., description="The ID of the note")

notes=[
    {"noteId":1,"note_title":"first title","note":"This is the first note in our list","Author":"Lewis"},
    {"noteId":2,"note_title":"second title","note":"This is the second note in our list","Author":"Lewiston"},
    {"noteId":3,"note_title":"third title","note":"This is the third note in our list","Author":"Leon"},
    {"noteId":4,"note_title":"fourth title","note":"This is the fourth note in our list","Author":"John"}
]

class Authorisation():
        def __call__(self, x_token:Annotated[str, Header()]) ->str:
            if x_token != "lewis":
                raise HTTPException(status_code=403, detail="Invalid token")
            return x_token

def background_tasks_function(note_title:str):
    print(f"Background task started for note: {note_title}")
    return f"This is a background task for note:{note_title}"

@app.post("/notes/")
async def create_note(note:Note, x_token:Annotated[str,Depends(Authorisation())], background_task:BackgroundTasks):
    noteId = len(notes) + 1
    new_note = note.dict()
    new_note["noteId"] = noteId
    notes.append(new_note)
    background_task.add_task(background_tasks_function, note_title=note.note_title)
    return {"message": "Note saved successfully", "noteId": noteId}



@app.get("/notes/")
async def get_note(x_token:Annotated[str,Depends(Authorisation())]):
    return notes

@app.get("/notes/{noteId}")
async def get_note_by_id(noteId:int,
    x_token:Annotated[str,Depends(Authorisation())]):
    for note in notes:
        if note["noteId"] == noteId:
            return note
    return {"error": "Note not found"}





