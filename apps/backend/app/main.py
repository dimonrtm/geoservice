# -*- coding: utf-8 -*-
"""
Created on Mon Dec 29 20:31:28 2025

@author: dimon
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.lifespan import lifespan


app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}
