from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic
import base64
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "YOUR_API_KEY_HERE")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/analyze-cv", methods=["POST"])
def analyze_cv():
    try:
        data = request.get_json()
        if not data or "pdf_base64" not in data:
            return jsonify({"error": "pdf_base64 field zaroori hai."}), 400

        pdf_base64 = data["pdf_base64"]

        try:
            base64.b64decode(pdf_base64)
        except Exception:
            return jsonify({"error": "Invalid PDF format."}), 400

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system="""You are a professional CV analyzer for students. Extract key information and return ONLY valid JSON with no markdown, no preamble, no backticks.
Schema:
{
  "name": "Full Name",
  "headline": "e.g. Computer Science Graduate | Python Developer",
  "experience_tags": ["tag1","tag2","tag3"],
  "skills": [{"label":"Skill","pct":85}],
  "match_score": 78,
  "subscores": {"skills":80,"experience":70,"education":85,"communication":75},
  "recommendations": ["Rec 1","Rec 2","Rec 3"]
}
Rules: max 5 skills (pct 0-100), max 6 experience_tags, exactly 3 recommendations, all scores 0-100.""",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_base64,
                            },
                        },
                        {
                            "type": "text",
                            "text": "Analyze this student CV and return the JSON analysis.",
                        },
                    ],
                }
            ],
        )

        raw = "".join(
            block.text for block in message.content if hasattr(block, "text")
        )
        clean = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean)

        return jsonify({"success": True, "data": result})

    except anthropic.APIError as e:
        return jsonify({"error": f"AI API error: {str(e)}"}), 500
    except json.JSONDecodeError as e:
        return jsonify({"error": f"JSON parse error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        if not data or "question" not in data or "cv_data" not in data:
            return jsonify({"error": "question aur cv_data dono zaroori hain."}), 400

        question = data["question"].strip()
        cv_data = data["cv_data"]
        history = data.get("history", [])

        if not question:
            return jsonify({"error": "Sawaal khali nahi hona chahiye."}), 400

        cv_text = json.dumps(cv_data)
        messages = history[-6:] + [{"role": "user", "content": question}]

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            system=f"""You are a helpful AI career advisor for students.
The student's CV analysis is: {cv_text}
Answer concisely in 2-4 sentences. Be encouraging and specific.
Reply in the same language the student uses (Urdu or English).""",
            messages=messages,
        )

        reply = "".join(
            block.text for block in message.content if hasattr(block, "text")
        )

        return jsonify({"success": True, "reply": reply})

    except anthropic.APIError as e:
        return jsonify({"error": f"AI API error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


if __name__ == "__main__":
    print("CV Analyzer backend chal raha hai...")
    print("URL: http://localhost:5000")
    print("Health check: http://localhost:5000/health")
    app.run(debug=True, host="0.0.0.0", port=5000)
