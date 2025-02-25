import socket
import os
import json
import traceback
import openai
from openai._streaming import Stream
from openai.types.chat import ChatCompletionChunk

MODEL = "llama3.1:8b"
ROLE = "system:You are an helpful assistant."

#TODO:E4.1 add the stream function
#fix it to extract line.choices[0].delta.content
#END TODO

class Chat:
    def __init__(self, args):

        host = args.get("OLLAMA_HOST", os.getenv("OLLAMA_HOST"))
        api_key = args.get("AUTH", os.getenv("AUTH"))
        base_url = f"https://{api_key}@{host}/v1"

        self.client = openai.OpenAI(
            base_url = base_url,
            api_key = api_key,
        )

        self.messages = []
        self.add(ROLE)

        #TODO:E4.1
        self.sock = args.get("STREAM_HOST")
        self.port = int(args.get("STREAM_PORT"))
        #END TODO

        print(f"{self.sock=}, {self.port=}")

    def add(self, msg):
        [role, content] = msg.split(":", maxsplit=1)
        self.messages.append({
            "role": role,
            "content": content,
        })

    def stream(self, res: Stream[ChatCompletionChunk]):
        out = ""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.sock, self.port))
            try:
                for line in res:
                    message_delta = line.choices[0].delta.content
                    msg = {"output": message_delta}
                    s.sendall(json.dumps(msg).encode('utf-8'))
                    out += str(message_delta)
            except Exception as e:
                traceback.print_exc(e)
                out = str(e)
        return out

    def complete(self):
        #TODO:E4.1
        # add stream: True
        res = self.client.chat.completions.create(
            model=MODEL,
            messages=self.messages,
            stream=True
        )
        # END TODO
        try:
            #TODO:E4.1 stream the result
            out = self.stream(res)
            #END TODO
            self.add(f"assistant:{out}")
        except:
            out = "error"
        return out

