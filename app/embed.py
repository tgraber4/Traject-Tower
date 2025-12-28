from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import json
from bs4 import BeautifulSoup
import os
import sys
import shutil

def get_resource_path(relative_path):
    """Get absolute path to bundled resource (works for dev and PyInstaller)"""
    try:
        # PyInstaller extracts files to a temp folder
        base_path = sys._MEIPASS
    except AttributeError:
        # Normal Python script
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def get_data_path(filename=""):
    """Return a writable path for storing user data."""

    applicationName = "TrajectTower"

    # “Elevate Your Career, One Step at a Time.”

    if sys.platform == "win32":
        base = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), applicationName)
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support/" + applicationName)
    else:
        base = os.path.expanduser("~/.local/share/" + applicationName)

    os.makedirs(base, exist_ok=True)
    return os.path.join(base, filename)


def get_copied_data_file_path(filename):
    """
    If the file doesn't exist in the user's data folder, copy it from bundled resources.
    Returns the full path to the writable file.
    """
    user_file_path = get_data_path(filename)

    if not os.path.exists(user_file_path):
        # Ensure all parent directories exist
        os.makedirs(os.path.dirname(user_file_path), exist_ok=True)
        
        bundled_file_path = get_resource_path(filename)
        if os.path.exists(bundled_file_path):
            shutil.copy(bundled_file_path, user_file_path)

    # Optional: validate file
    if not is_valid_data_file_path(filename):
        raise IOError(f"Cannot access or write to {user_file_path}")

    return user_file_path

def is_valid_data_file_path(filename):
    """
    Check if a file is a valid data file.
    Returns True if the file exists and is writable, False otherwise.
    """
    path = get_data_path(filename)
    return os.path.isfile(path) and os.access(path, os.W_OK)



jobsDataJsonFilePath = get_data_path("data/jobs_data.json")
logsJsonFilePath = get_data_path("data/logs.json")

def normalize(text: str) -> str:
    """
    Basic text normalization to reduce noise before embedding.
    """
    return " ".join(text.lower().split())


def getEmailInput(emailList, emailID):
    

    html = emailList[emailID]["body"]

    soup = BeautifulSoup(html, "lxml")

    text = soup.get_text(separator="\n", strip=True)

    emailInput = emailList[emailID]["subject"] + "\n" + text

    emailInput = emailInput.lower()

    return emailInput


def getJobFileContent():
    if not os.path.exists(jobsDataJsonFilePath):
        raise ValueError("jobs data json missing")
        return None

    with open(jobsDataJsonFilePath, "r") as f:
        return json.load(f)

def getJobText():
    data = getJobFileContent()

    job_texts = []

    for j in range(len(data)):
        job_texts.append("Company: " + data[j]["company"] + " | Role: " + data[j]["title"])

    return job_texts

def getLogFileContent():
    data = {}
    data["emailsViewed"] = []
    data["JobsUpdated"] = []

    if not os.path.exists(logsJsonFilePath):
        return data
    
    with open(logsJsonFilePath, "r") as f:
        return json.load(f)

def updateJobStatus(index, updatedStatus):
    data = getJobFileContent()

    data[index]["status"] = updatedStatus

    with open(jobsDataJsonFilePath, "w") as f:
        json.dump(data, f, indent=2)

def updateEmailLog(inputEmail):
    # update emailsViewed list in logs
    data = getLogFileContent()

    data["emailsViewed"].append(inputEmail)

    with open(logsJsonFilePath, "w") as f:
        json.dump(data, f, indent=2)

def updateJobsUpdatedLog(jobInput):
    # update updated list in logs
    data = getLogFileContent()

    data["JobsUpdated"].append(jobInput)

    with open(logsJsonFilePath, "w") as f:
        json.dump(data, f, indent=2)

def emailContainedInLog(emailSubject, emailDate):
    data = getLogFileContent()
    
    for i in range(len(data["emailsViewed"])):
        if (data["emailsViewed"][i]["subject"] == emailSubject and data["emailsViewed"][i]["date"] == emailDate):
            return True
    return False

# ---- Embedding ----

def runEmbeddings(emailList):
    # Load embedding model
    model = SentenceTransformer("all-MiniLM-L6-v2")

    invalidEmails = []
    emailsUpdated = 0
    job_info = getJobFileContent()
    job_texts = getJobText()
    for i in range(len(emailList)):
        emailInput = getEmailInput(emailList, i)

        # skip if email is already checked
        if (emailContainedInLog(emailList[i]["subject"], emailList[i]["date"])):
            continue

        texts = [normalize(emailInput)] + [normalize(t) for t in job_texts]
        embeddings = model.encode(texts)

        email_embedding = embeddings[0]
        job_embeddings = embeddings[1:]

        # ---- Similarity ----
        scores = cosine_similarity([email_embedding], job_embeddings)[0]

        best_index = scores.argmax()
        best_score = scores[best_index]

        # ---- Decision ----
        THRESHOLD = 0.5

        if best_score < THRESHOLD:
            result = -1
        else:
            result = best_index

        # ---- Debug output (optional, but recommended while tuning) ----
        print("Similarity scores:")
        for k, score in enumerate(scores):
            print(f"{k}: {job_texts[k]} -> {score:.3f}")

        print("\nFinal result:", result)
        print("\n\n")
        
        if (result == -1):
            invalidEmails.append(emailList[i])
        else:
            emailsUpdated+=1
            updateJobStatus(result, emailList[i]["type"])
            updateJobsUpdatedLog({"company": job_info[result]["company"], "title": job_info[result]["title"], "type": emailList[i]["type"]})
        updateEmailLog({"subject": emailList[i]["subject"], "date": emailList[i]["date"]})

    return invalidEmails, emailsUpdated