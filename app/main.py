from fastapi import FastAPI
import json

app = FastAPI(title="Job Application Agent")


@app.get("/")
def root():
    return {"message": "Job Application Agent is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/candidate")
def get_candidate():
    with open("candidate/profile.json", "r") as file:
        profile = json.load(file)

    return profile