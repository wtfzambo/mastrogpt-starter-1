import base64
import os, requests as req
import bucket
import vision
import time

USAGE = "Please upload a picture and I will tell you what I see"
FORM = [
  {
    "label": "any pics?",
    "name": "pic",
    "required": "true",
    "type": "file"
  },
]

def form(args):
  res = {}
  out = USAGE
  inp = args.get("input", "")
  bkt = bucket.Bucket(args)

  if type(inp) is dict and "form" in inp:
    img = inp.get("form", {}).get("pic", "")
    print(f"uploaded size {len(img)}")

    data = base64.b64decode(img)
    img_key = f"imgs/{time.time_ns()}.jpg"
    bkt.write(key=img_key, body=data)

    vis = vision.Vision(args)
    out = vis.decode(img)

    url = bkt.exturl(img_key, 3600)
    res['html'] = f'<img src="{url}">'

  res['form'] = FORM
  res['output'] = out
  return res
