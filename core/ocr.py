import base64
import json
from io import BytesIO
from typing import Dict

from PIL import Image

from .config import client_qwen  

prompt = """
You are a medical prescription OCR assistant.

PRIMARY GOAL:
From the prescription image, extract ONLY the medications and their doses. Ignore patient info, doctor info, addresses, dates, and pharmacy details.

CRITICAL RULES:
- DO NOT GUESS.
- DO NOT USE MEDICAL KNOWLEDGE to correct or complete drug names or doses.
- Read the handwriting as literally as possible.
- If you are not sure about a part of the text, keep it in raw_text and set the structured fields to null.
- Prefer null over guessing.
- Do NOT explain anything.
- Do NOT output markdown.
- Output MUST be a single valid JSON object.

INTERPRETATION RULES FOR FIELDS:
- "strength": concentration or strength of the medicine itself
  e.g., "250 mg", "125 mg/5 ml", "3%", "500 mg tablet"

- "dose": the amount to be taken each time
  e.g., "4 ml", "1 tablet", "10 drops"

- "frequency": how often the dose is taken
  e.g., "tds", "bd", "2x daily", "every 6 hours"

- "instructions": extra notes like "SOS", "if needed", "as advised"

If a line only contains a general instruction (e.g., "If as advised x 5d"),
and does NOT contain a medicine name, treat it as a note and do NOT add a
new medication entry. Instead, describe it briefly in illegible_details.


WHAT TO EXTRACT:
- Every line that looks like a drug + strength + directions (“Sig”) or dose.
- For each such line, keep the exact raw text, plus a structured breakdown IF it is clear.

OUTPUT FORMAT (JSON ONLY):

{

  "medications": [
    {
      "raw_text": string,             // exact text as you read it from the prescription
      "drug_name": string or null,    // as written, not corrected
      "strength": string or null,     // e.g. "500 mg", "3 gr", "3%", "5 ml"
      "dose": string or null,         // e.g. "1 tablet", "1 tsp", "20 drops"
      "frequency": string or null,    // e.g. "every 8 hours", "3 times daily"
      "duration": string or null,     // e.g. "5 days", "1 week"
      "instructions": string or null, // other directions like "for cough", "after meals"
      "confidence": number            // 0–1
    }
  ],
  "illegible": boolean,
  "illegible_details": string or null
}

IMPORTANT:
- If a prescription has only one medication, medications will contain one item.
- If no medication or dose can be reliably read, return an empty medications list and set illegible = true.


"""

def img_to_byte(path):
  img = Image.open(path).convert("RGB")
  byte = BytesIO()
  img.save(byte,format="PNG")
  base64_img = base64.b64encode(byte.getvalue()).decode("utf-8")
  return f"data:image/png;base64,{base64_img}"


def call_qwen_model(image_path):
  data_url = img_to_byte(image_path)
  response = client_qwen.chat.completions.create(
      messages =[
          {"role":"user",
           "content":[
               {"type":"image_url","image_url":{"url":data_url}},
               {"type":"text","text":prompt}
           ]
           }
      ],
      max_tokens = 2048, 
      temperature = 0.0,
  )
  return json.loads(response.choices[0].message.content)