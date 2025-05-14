import os
import json
import hashlib
from better_profanity import profanity
from starlette.requests import Request
from starlette.responses import Response
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from starlette.middleware.base import BaseHTTPMiddleware
from firewall.token_utils import num_tokens_from_string


analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()
profanity.load_censor_words()

TOKEN_WARNING_THRESHOLD = int(os.getenv("TOKEN_LIMIT", 16000) * 0.8)


class PIIFirewallMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.endswith("/ask") and request.method == "POST":
            body_bytes = await request.body()
            body = json.loads(body_bytes)

            prompt = body.get("message", "")

            prompt_token_count = num_tokens_from_string(prompt)
            if prompt_token_count > TOKEN_WARNING_THRESHOLD:
                print(
                    f"[WARNING] Prompt uses {prompt_token_count} tokens — nearing limit.")

            if prompt:
                results = analyzer.analyze(text=prompt, language="en")
                anonymized = anonymizer.anonymize(
                    text=prompt, analyzer_results=results
                )
                original_hash = hashlib.sha256(prompt.encode()).hexdigest()
                print(f"Original hash: {original_hash}")
                print(f"Redacted Prompt: {anonymized.text}")
                body["message"] = anonymized.text
                request._body = json.dumps(body).encode("utf-8")

        response = await call_next(request)

        if request.url.path.endswith("/ask") and response.status_code == 200:
            resp_body = [section async for section in response.body_iterator]
            decoded = b"".join(resp_body).decode()
            data = json.loads(decoded)

            output_text = data.get("text", "") or data.get(
                "candidates", [{}])[0].get("content", "")

            pii_results = analyzer.analyze(text=output_text, language="en")
            if pii_results:
                redacted = anonymizer.anonymize(
                    text=output_text, analyzer_results=pii_results).text
                data["text"] = redacted
                data["output_pii_redacted"] = True
            else:
                data["output_pii_redacted"] = False

            if profanity.contains_profanity(output_text):
                data["text"] = profanity.censor(data["text"])
                data["profanity_detected"] = True
            else:
                data["profanity_detected"] = False

            new_body = json.dumps(data)
            return Response(content=new_body, media_type="application/json")

        return response
