from textwrap import dedent
import re, os, requests as req
#MODEL = "llama3.1:8b"
MODEL = "phi4:14b"

# queen rook knight bishop

FORM = [
  {
    "label": "With a queen",
    "name": "queen",
    "required": "false",
    "type": "checkbox"
  },
  {
    "label": "With a rook",
    "name": "rook",
    "required": "false",
    "type": "checkbox"
  },
  {
    "label": "With a knight",
    "name": "knight",
    "required": "false",
    "type": "checkbox"
  },
  {
    "label": "With a bishop",
    "name": "bishop",
    "required": "false",
    "type": "checkbox"
  },
]

def chat(args, inp):
  host = args.get("OLLAMA_HOST", os.getenv("OLLAMA_HOST"))
  auth = args.get("AUTH", os.getenv("AUTH"))
  url = f"https://{auth}@{host}/api/generate"
  msg = { "model": MODEL, "prompt": inp, "stream": False}
  res = req.post(url, json=msg).json()
  out = res.get("response", "error")
  return  out

def extract_fen(out):
  pattern = r"([rnbqkpRNBQKP1-8]+\/){7}[rnbqkpRNBQKP1-8]+"
  fen = None
  m = re.search(pattern, out, re.MULTILINE)
  if m:
    fen = m.group(0)
  return fen

def puzzle(args):
  out = "If you want to see a chess puzzle, type 'puzzle'. To display a fen position, type 'fen <fen string>'."
  inp = args.get("input", "")
  res = {}

  print(f"{inp=}")

  if inp == "puzzle":
    res["form"] = FORM
    out = "Select which pieces you want to include in the puzzle"

  elif type(inp) is dict and "form" in inp:
    data: dict = inp["form"]
    selection = [k for k, v in data.items() if v == "true"]
    inp = dedent(f"""
      generate a chess puzzle in FEN format, featuring at least one for each of the following pieces:
      {", ".join(selection)}.
    """)
    out = chat(args, inp)
    fen = extract_fen(out)
    if fen:
       print(fen)
       res['chess'] = fen
    else:
      out = "Bad FEN position."

  elif inp.startswith("fen"):
    fen = extract_fen(inp)
    if fen:
       out = "Here you go."
       res['chess'] = fen

  elif inp != "":
    out = chat(args, inp)
    fen = extract_fen(out)
    print(out, fen)
    if fen:
      res['chess'] = fen

  res["output"] = out
  return res
