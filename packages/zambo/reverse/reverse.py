def reverse(args):
  inp = args.get("input", "")
  out = "Please provide some input"
  if inp != "":
    out = inp[::-1]
  return { "output": out }
