from openai import OpenAI
#from settings import settings

chiave="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"

class LLMModel:
    def __init__(self):
        self.client= OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=chiave,
                    default_headers={
                                    "HTTP-Referer": "http://localhost",   
                                    "X-Title": "provenance-tool",         
                                    }
                    )

    def chat(self, prompt:str):
        response = self.client.chat.completions.create(
                                            model="mistralai/devstral-2512:free",
                                            messages=[{ "role": "user", "content": prompt}]
                                        )

        return response.choices[0].message.content
    




if __name__ == "__main__":
    llm_model = LLMModel()
    response = llm_model.chat("come stai?")
    print(response)

