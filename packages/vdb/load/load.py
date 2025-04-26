import json
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


def tokenize(text: str):
    tokens = text.split()

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if re.match(r"\d{1,2}[/-]\d{1,2}[/-]\d{4}", token):
            pass

        elif re.match(r"\w+'s", token):
            token = re.sub(r"(\w+)'s", r"\1 's", token)

        elif re.match(r"\w+'\w+", token):
            token = token.replace("'", "")

        elif re.match(r"\w+-\w+", token):
            pass

        elif re.match(r"\d+(,\d+)*", token):
            pass

        else:
            token = re.sub(r"([^\w\s]+)", r" \1 ", token)

        tokens[i] = token
        i += 1

    return tokens


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
                tokens = tokenize(text_content)
                out = json.dumps(tokens)
            else:
                out = "No readable text content found on the page"
        except req.RequestException as e:
            out = f"Error fetching the webpage: {str(e)}"

    elif inp != "":
        res = db.insert(inp)
        out = "Inserted "
        out += " ".join([str(x) for x in res.get("ids", [])])

    return {"output": out}
