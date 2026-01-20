import anthropic
import json
import os
import time
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


class ClaudeServiceError(Exception):
    """Custom exception for Claude service errors"""
    pass


class ClaudeService:
    def __init__(self):
        try:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            print(f"Initializing Claude with API key: {api_key[:20] if api_key else 'NONE'}...")

            if not api_key:
                raise ClaudeServiceError("ANTHROPIC_API_KEY not found in environment")

            if not api_key.startswith('sk-ant-'):
                raise ClaudeServiceError("Invalid Anthropic API key format")

            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = 'claude-3-haiku-20240307'
            self.max_retries = 3
            self.retry_delay = 2  # seconds

        except anthropic.AuthenticationError as e:
            print(f"Claude authentication error: {e}")
            raise ClaudeServiceError("Invalid Anthropic API key")
        except Exception as e:
            print(f"Failed to initialize Claude service: {e}")
            raise ClaudeServiceError(f"Claude initialization failed: {str(e)}")

    def _make_api_call(self, messages: list, max_tokens: int, retries: int = None) -> str:
        """Make API call with retry logic"""
        retries = retries if retries is not None else self.max_retries

        for attempt in range(retries):
            try:
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    messages=messages
                )

                if not message.content:
                    raise ClaudeServiceError("Empty response from Claude API")

                return message.content[0].text

            except anthropic.RateLimitError as e:
                print(f"Rate limit error (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    wait_time = self.retry_delay * (attempt + 1)
                    print(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    raise ClaudeServiceError("Rate limit exceeded. Please try again later.")

            except anthropic.APIConnectionError as e:
                print(f"API connection error (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise ClaudeServiceError("Unable to connect to Claude API. Please check your internet connection.")

            except anthropic.APIStatusError as e:
                print(f"API status error: {e.status_code} - {e.message}")
                if e.status_code >= 500:
                    if attempt < retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                raise ClaudeServiceError(f"Claude API error: {e.message}")

            except anthropic.AuthenticationError as e:
                raise ClaudeServiceError("Invalid API key. Please check your Anthropic API key.")

            except Exception as e:
                print(f"Unexpected error in Claude API call: {type(e).__name__}: {e}")
                if attempt < retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise ClaudeServiceError(f"Claude API call failed: {str(e)}")

        raise ClaudeServiceError("Max retries exceeded")

    def _parse_json_response(self, response_text: str) -> dict:
        """Parse JSON from response text with error handling"""
        if not response_text:
            return {}

        try:
            # Try direct JSON parse first
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from response
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")

        return {}

    def analyze_context_for_questions(self, context: str, questions: list) -> list:
        """
        Analyze context and suggest answers for questions.
        Returns list of {question_id, suggested_answer, confidence, source}
        Processes questions in batches to avoid output token limits.
        """
        if not context or not context.strip():
            raise ClaudeServiceError("Context is required for analysis")

        if not questions:
            raise ClaudeServiceError("Questions are required for analysis")

        all_responses = []
        batch_size = 15  # Process 15 questions at a time
        total_batches = (len(questions) + batch_size - 1) // batch_size
        failed_batches = []

        # Process questions in batches
        for i in range(0, len(questions), batch_size):
            batch = questions[i:i + batch_size]
            batch_num = (i // batch_size) + 1

            print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} questions)")

            try:
                batch_responses = self._analyze_batch(context, batch)
                all_responses.extend(batch_responses)
                print(f"  -> Batch {batch_num} completed: {len(batch_responses)} responses")
            except Exception as e:
                print(f"  -> Batch {batch_num} failed: {e}")
                failed_batches.append(batch_num)
                # Continue with other batches even if one fails

        if failed_batches:
            print(f"Warning: {len(failed_batches)} batches failed: {failed_batches}")

        print(f"Total responses collected: {len(all_responses)}")
        return all_responses

    def _analyze_batch(self, context: str, questions: list) -> list:
        """Analyze a single batch of questions."""
        if not questions:
            return []

        questions_text = "\n".join([
            f"{i+1}. [{q['id']}] {q['question']}"
            for i, q in enumerate(questions)
        ])

        # Truncate context if too long (leave room for response)
        max_context_length = 30000
        truncated_context = context[:max_context_length]
        if len(context) > max_context_length:
            truncated_context += "\n\n[Context truncated due to length...]"

        prompt = f"""You are a Product Management expert. Analyze the context and answer these {len(questions)} questions.

CONTEXT:
{truncated_context}

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
            response_text = self._make_api_call(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4096
            )

            result = self._parse_json_response(response_text)
            responses = result.get('responses', [])

            # Validate response format
            valid_responses = []
            for resp in responses:
                if resp.get('question_id') and resp.get('suggested_answer') is not None:
                    valid_responses.append({
                        'question_id': resp['question_id'],
                        'suggested_answer': resp.get('suggested_answer', ''),
                        'confidence': resp.get('confidence', 'low'),
                        'source_hint': resp.get('source_hint', '')
                    })

            return valid_responses

        except ClaudeServiceError:
            raise
        except Exception as e:
            print(f"Error analyzing batch: {type(e).__name__}: {e}")
            return []

    def generate_prd(self, responses: dict, prd_template: str) -> str:
        """
        Generate a complete PRD based on question responses.
        """
        if not responses:
            raise ClaudeServiceError("Responses are required to generate PRD")

        # Format responses for the prompt
        responses_text = ""
        response_count = 0

        for section_id, section_responses in responses.items():
            responses_text += f"\n=== {section_id} ===\n"
            for r in section_responses:
                responses_text += f"Q: {r.get('question', 'N/A')}\n"
                responses_text += f"A: {r.get('response', 'N/A')}\n\n"
                response_count += 1

        if response_count == 0:
            raise ClaudeServiceError("No valid responses found to generate PRD")

        # Truncate template if too long
        max_template_length = 10000
        truncated_template = prd_template[:max_template_length] if prd_template else ""

        prompt = f"""You are a senior Product Manager creating a comprehensive PRD (Product Requirements Document).

Based on the following question responses from our pre-PRD clarity exercise, generate a complete PRD document.

QUESTION RESPONSES:
{responses_text}

PRD TEMPLATE STRUCTURE TO FOLLOW:
{truncated_template}

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
            prd_content = self._make_api_call(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=Config.MAX_TOKENS
            )

            if not prd_content or len(prd_content.strip()) < 100:
                raise ClaudeServiceError("Generated PRD content is too short or empty")

            return prd_content

        except ClaudeServiceError:
            raise
        except Exception as e:
            print(f"Claude API error generating PRD: {e}")
            raise ClaudeServiceError(f"Failed to generate PRD: {str(e)}")

    def refine_prd_section(self, section_name: str, current_content: str,
                          additional_context: str) -> str:
        """
        Refine a specific section of the PRD with additional context.
        """
        if not section_name:
            raise ClaudeServiceError("Section name is required")
        if not current_content:
            raise ClaudeServiceError("Current content is required")

        prompt = f"""You are a senior Product Manager. Please refine and improve the following PRD section.

SECTION: {section_name}

CURRENT CONTENT:
{current_content}

ADDITIONAL CONTEXT/FEEDBACK:
{additional_context or 'No additional context provided'}

Please provide an improved version of this section that:
1. Incorporates the additional context
2. Maintains professional PRD standards
3. Is clear, specific, and actionable
4. Uses appropriate markdown formatting

Return only the improved section content:"""

        try:
            refined_content = self._make_api_call(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048
            )

            return refined_content if refined_content else current_content

        except ClaudeServiceError as e:
            print(f"Claude API error refining section: {e}")
            # Return original content on error instead of failing
            return current_content
        except Exception as e:
            print(f"Unexpected error refining section: {e}")
            return current_content


# Singleton instance with error handling
try:
    claude_service = ClaudeService()
except Exception as e:
    print(f"Warning: Claude service initialization failed: {e}")
    claude_service = None
