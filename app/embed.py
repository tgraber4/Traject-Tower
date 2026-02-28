import json
from bs4 import BeautifulSoup
import os

from app.paths import get_data_path


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
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
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