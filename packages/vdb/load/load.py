import re

import requests as req
import vdb
from bs4 import BeautifulSoup

USAGE = """Welcome to the Vector DB Loader.
Write text to insert in the DB.
Start with * to do a vector search in the DB.
Start with ! to remove text with a substring.
Start with http:// or https:// to load text from a webpage.
"""


def sent_tokenize(text: str):
    MAX_BYTES = 1000  # Safety margin below 1024 bytes

    # First split into sentences using the regex
    sentences = re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s", text)
    result = []

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # Convert to bytes to check the actual size
        sentence_bytes = sentence.encode("utf-8")

        if len(sentence_bytes) <= MAX_BYTES:
            result.append(sentence)
        else:
            # If sentence is too long, split it up
            current = ""
            for word in sentence.split():
                test = (current + " " + word).strip()
                if len(test.encode("utf-8")) <= MAX_BYTES:
                    current = test
                else:
                    if current:
                        result.append(current)
                    current = word
            if current:
                result.append(current)

    return result


def load(args):
    collection = args.get("COLLECTION", "default")
    out = f"{USAGE}Current colletion is {collection}"
    inp = str(args.get("input", ""))
    db = vdb.VectorDB(args)

    if inp.startswith("*"):
        if len(inp) == 1:
            out = "please specify a search string"
        else:
            res = db.vector_search(inp[1:])
            if len(res) > 0:
                out = "Found:\n"
                for i in res:
                    out += f"({i[0]:.2f}) {i[1]}\n"
            else:
                out = "Not found"

    elif inp.startswith("!"):
        count = db.remove_by_substring(inp[1:])
        out = f"Deleted {count} records."

    elif inp.startswith("https://") or inp.startswith("http://"):
        try:
            page = req.get(inp)
            page.raise_for_status()  # Raise an exception for bad status codes
            soup = BeautifulSoup(page.text, "html.parser")
            text_content = soup.get_text(" ", strip=True)
            if text_content:
                sentences = sent_tokenize(text_content)
                for s in sentences:
                    res = db.insert(s)
                    out = "Inserted "
                    out += " ".join([str(x) for x in res.get("ids", [])])
            else:
                out = "No readable text content found on the page"
        except req.RequestException as e:
            out = f"Error fetching the webpage: {str(e)}"

    elif inp != "":
        res = db.insert(inp)
        out = "Inserted "
        out += " ".join([str(x) for x in res.get("ids", [])])

    return {"output": out}
