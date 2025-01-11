from fastapi import FastAPI, Request, Depends, HTTPException,status
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from jose import JWTError, jwt
from sqlalchemy import create_engine, select
from typing import Optional
from datetime import datetime, date, time, timedelta
from apifuncs import Page_FUNCS

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


class URLdata(BaseModel):
    url: str

@app.post("/api/link/")
async def get_medium_score(link_data: URLdata):
    return Page_FUNCS.get_medium_content_Scores(link_data.url)

@app.post("/api/website/scores/bylink/")
async def website_score_by_link(link_data: URLdata):
    return Page_FUNCS.get_page_scores(link_data.url)

