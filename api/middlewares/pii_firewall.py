import os
import json
import hashlib
from better_profanity import profanity
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from starlette.middleware.base import BaseHTTPMiddleware
from firewall.token_utils import num_tokens_from_string
from firewall.scorer import compute_risk_score
from firewall.prompt_injection import (
    detect_prompt_injection,
    get_triggered_phrases
)


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
                pii_entities = [res.entity_type for res in results]
                risk_score = compute_risk_score(prompt, pii_entities)

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

            print(f"Risk Score: {risk_score}")
            if detect_prompt_injection(prompt):
                print(f"[BLOCKED] Prompt injection attempt detected: {get_triggered_phrases(prompt)}")
                print(f"Risk Score: {risk_score}")
                if risk_score >= 25:
                    data["risk_score"] = risk_score
                    data["error"] = "Prompt injection attempt detected."
                    data["triggered_phrases"] = get_triggered_phrases(prompt)

            new_body = json.dumps(data)
            return Response(content=new_body, media_type="application/json")

        return response
