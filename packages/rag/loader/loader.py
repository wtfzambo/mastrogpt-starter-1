import base64
import os
import time

import bucket
import requests
import vdb

USAGE = """Welcome to the Vector DB Loader.
Write text to insert in the DB.
Use `@[<coll>]` to select/create a collection and show the collections.
Use `*<string>` to vector search the <string>  in the DB.
Use `#<limit>`  to change the limit of searches.
Use `!<substr>` to remove text with `<substr>` in collection.
Use `!![<collection>]` to remove `<collection>` (default current) and switch to default.
Use `picture` to upload a picture.

"""

MODEL = "llama3.2-vision:11b"
# Add image loading capabilities here:
#   1. ✅ add condition in the loader
#   2. ✅ put form
#   3. ✅ load image and parse it with LLM
#   4. save image description, embeddings etc... in VDB, as well as img address
#   5. somehow do a RAG to get image out
#   use existing vision package to take example


class Vision:
    def __init__(self, args):
        host = args.get("OLLAMA_HOST", os.getenv("OLLAMA_HOST"))
        auth = args.get("OLLAMA_TOKEN", os.getenv("AUTH"))
        self.url = f"https://{auth}@{host}/api/chat"

    def decode(self, img):
        msg = {
            "model": MODEL,
            "messages": [
                {"role": "user", "content": "what is in this image?", "images": [img]}
            ],
            "stream": False,
        }
        res = requests.post(self.url, json=msg).json()
        return res.get("message", {}).get("content", "")


def loader(args):
    # print(args)
    # get state: <collection>[:<limit>]
    collection = "default"
    limit = 30
    sp = args.get("state", "").split(":")
    if len(sp) > 0 and len(sp[0]) > 0:
        collection = sp[0]
    if len(sp) > 1:
        try:
            limit = int(sp[1])
        except Exception:
            pass
    print(collection, limit)

    out = f"{USAGE}Current collection is {collection} with limit {limit}"
    db = vdb.VectorDB(args, collection)
    inp = args.get("input", "")

    res = {}

    if type(inp) is str:
        # select collection
        if inp.startswith("@"):
            out = ""
            if len(inp) > 1:
                collection = inp[1:]
                out = f"Switched to {collection}.\n"
            out += db.setup(collection)

        # set size of search
        elif inp.startswith("#"):
            try:
                limit = int(inp[1:])
            except Exception:
                pass
            out = f"Search limit is now {limit}.\n"

        # run a query
        elif inp.startswith("*"):
            search = inp[1:]
            if search == "":
                search = " "
            result = db.vector_search(search, limit=limit)
            if len(result) > 0:
                out = "Found:\n"
                for i in result:
                    out += f"({i[0]:.2f}) {i[1]}\n"
            else:
                out = "Not found"

        # remove a collection
        elif inp.startswith("!!"):
            if len(inp) > 2:
                collection = inp[2:].strip()
            out = db.destroy(collection)
            collection = "default"

        # remove content
        elif inp.startswith("!"):
            count = db.remove_by_substring(inp[1:])
            out = f"Deleted {count} records."

        # give form to add an image
        elif inp.startswith("picture"):
            FORM = [
                {
                    "label": "Add an image",
                    "name": "pic",
                    "required": "true",
                    "type": "file",
                }
            ]
            res["form"] = FORM
            out = "Upload a picture. You can later search it by giving a description."

        elif inp != "":
            out = "Inserted "
            lines = [inp]
            if args.get("options", "") == "splitlines":
                lines = inp.split("\n")
            for line in lines:
                if line == "":
                    continue
                result = db.insert(line)
                out += "\n".join([str(x) for x in result.get("ids", [])])
                out += "\n"

    # upload the image
    elif type(inp) is dict and "form" in inp:
        bkt = bucket.Bucket(args)
        img = inp.get("form", {}).get("pic", "")
        data = base64.b64decode(img)
        img_key = f"imgs/{time.time_ns()}.jpg"
        bkt.write(key=img_key, body=data)

        vis = Vision(args)
        out = vis.decode(img)

        url = bkt.exturl(img_key, 3600)
        res["html"] = f'<img src="{url}">'

    res["output"] = out
    res["state"] = f"{collection}:{limit}"
    return res
