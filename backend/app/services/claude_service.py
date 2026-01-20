import anthropic
import json
import os
from pathlib import Path
from dotenv import dotenv_values

# Load env values directly from the backend directory
backend_dir = Path(__file__).parent.parent.parent
env_path = backend_dir / '.env'
env_config = dotenv_values(env_path)

# Set them in os.environ so other modules can access
for key, value in env_config.items():
    if value:
        os.environ[key] = value

print(f"Loaded {len(env_config)} env vars from: {env_path}")

from app.config import Config


class ClaudeService:
    def __init__(self):
        api_key = os.getenv('ANTHROPIC_API_KEY')
        print(f"Initializing Claude with API key: {api_key[:20] if api_key else 'NONE'}...")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = 'claude-3-haiku-20240307'

    def analyze_context_for_questions(self, context: str, questions: list) -> list:
        """
        Analyze context and suggest answers for questions.
        Returns list of {question_id, suggested_answer, confidence, source}
        Processes questions in batches to avoid output token limits.
        """
        all_responses = []
        batch_size = 15  # Process 15 questions at a time

        # Process questions in batches
        for i in range(0, len(questions), batch_size):
            batch = questions[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(questions) + batch_size - 1) // batch_size

            print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} questions)")

            batch_responses = self._analyze_batch(context, batch)
            all_responses.extend(batch_responses)

        print(f"Total responses collected: {len(all_responses)}")
        return all_responses

    def _analyze_batch(self, context: str, questions: list) -> list:
        """Analyze a single batch of questions."""
        questions_text = "\n".join([
            f"{i+1}. [{q['id']}] {q['question']}"
            for i, q in enumerate(questions)
        ])

        prompt = f"""You are a Product Management expert. Analyze the context and answer these {len(questions)} questions.

CONTEXT:
{context[:30000]}

QUESTIONS:
{questions_text}

Return JSON with this EXACT format (no extra text):
{{"responses": [{{"question_id": "X.X.X", "suggested_answer": "your answer", "confidence": "high|medium|low", "source_hint": "source"}}]}}

Rules:
- Answer ONLY the questions listed above
- Use "Information not found" if context doesn't cover it
- Keep answers concise but informative
- confidence: high=directly stated, medium=inferred, low=partial match"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            # Parse JSON response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                result = json.loads(json_str)
                responses = result.get('responses', [])
                print(f"  -> Got {len(responses)} responses")
                return responses

            print(f"  -> Could not parse JSON")
            return []
        except Exception as e:
            print(f"  -> Error: {type(e).__name__}: {e}")
            return []

    def generate_prd(self, responses: dict, prd_template: str) -> str:
        """
        Generate a complete PRD based on question responses.
        """
        # Format responses for the prompt
        responses_text = ""
        for section_id, section_responses in responses.items():
            responses_text += f"\n=== {section_id} ===\n"
            for r in section_responses:
                responses_text += f"Q: {r.get('question', 'N/A')}\n"
                responses_text += f"A: {r.get('response', 'N/A')}\n\n"

        prompt = f"""You are a senior Product Manager creating a comprehensive PRD (Product Requirements Document).

Based on the following question responses from our pre-PRD clarity exercise, generate a complete PRD document.

QUESTION RESPONSES:
{responses_text}

PRD TEMPLATE STRUCTURE TO FOLLOW:
{prd_template[:10000]}

INSTRUCTIONS:
1. Fill in every section of the PRD template with relevant information from the responses
2. If information is missing for a section, add a placeholder "[TO BE COMPLETED]"
3. Maintain professional tone and formatting
4. Use markdown formatting throughout
5. Include all standard PRD sections: Executive Summary, Problem Definition, User Research, Strategic Context, Goals & Metrics, Solution Overview, User Stories, UI/UX Specs, Technical Requirements, etc.
6. Cross-reference information between sections for consistency
7. Add appropriate tables where the template shows them

Generate the complete PRD in markdown format:"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=Config.MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}]
            )

            return message.content[0].text
        except Exception as e:
            print(f"Claude API error generating PRD: {e}")
            return f"# Error Generating PRD\n\nAn error occurred: {str(e)}"

    def refine_prd_section(self, section_name: str, current_content: str,
                          additional_context: str) -> str:
        """
        Refine a specific section of the PRD with additional context.
        """
        prompt = f"""You are a senior Product Manager. Please refine and improve the following PRD section.

SECTION: {section_name}

CURRENT CONTENT:
{current_content}

ADDITIONAL CONTEXT/FEEDBACK:
{additional_context}

Please provide an improved version of this section that:
1. Incorporates the additional context
2. Maintains professional PRD standards
3. Is clear, specific, and actionable
4. Uses appropriate markdown formatting

Return only the improved section content:"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )

            return message.content[0].text
        except Exception as e:
            print(f"Claude API error refining section: {e}")
            return current_content


claude_service = ClaudeService()
