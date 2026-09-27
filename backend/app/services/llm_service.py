from google import genai
from app.config import settings

class LLMService:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False

    def generate(self, prompt: str, context: str = "") -> str:
        if not self.enabled:
            return "AI service not configured. Please add GEMINI_API_KEY to your .env file."
        full_prompt = prompt
        if context:
            full_prompt = f"Context information:\n{context}\n\nUser question: {prompt}\n\nAnswer based on the context above. If the context is insufficient, say so."
        try:
            response = self.client.models.generate_content(
                model="gemini-3.8-flash",
                contents=full_prompt,
            )
            return response.text
        except Exception as e:
            return f"AI error: {str(e)}"

    def explain_opportunity(self, opportunity_data: dict) -> str:
        prompt = f"""You are an innovation analyst. Explain why this opportunity scored the way it did.
Title: {opportunity_data.get('title')}
Demand: {opportunity_data.get('demand_score')}
Research Gap: {opportunity_data.get('research_gap_score')}
Trend: {opportunity_data.get('trend_score')}
Final Score: {opportunity_data.get('opportunity_score')}
Provide a concise 3-4 sentence explanation."""
        return self.generate(prompt)
