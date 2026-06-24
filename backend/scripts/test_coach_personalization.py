import os
import sys

# Ensure backend directory is in path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

from google import genai
from google.genai import types
from dotenv import load_dotenv

# We can import the coach logic
from app.services.coach_service import get_coach_context, SYSTEM_PROMPT
from app.core.config import settings

api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

class MockUser:
    def __init__(self, age_group, country):
        self.age_group = age_group
        self.country = country
        self.city = "Test City"

class MockInputs:
    def __init__(self, diet_type, transport_mode):
        self.diet_type = diet_type
        self.transport_mode = transport_mode

def run_test(scenario_name, user, assessment_dict, inputs):
    print(f"\n{'='*50}\nSCENARIO: {scenario_name}\n{'='*50}")
    
    context = get_coach_context(user, assessment_dict, inputs, "No goals")
    
    context_prompt = f"{context}\n\nUser Message: What are three things I can do this week to reduce my footprint?"
    print("\n--- INJECTED CONTEXT ---")
    print(context_prompt)
    print("------------------------\n")

if __name__ == "__main__":
    # Scenario 1: Student in Ahmedabad, India — motorcycle user, mixed diet
    user1 = MockUser("student", "India")
    assessment1 = {"total_emission": 1.2, "transport": 0.4, "energy": 0.2, "food": 0.5, "waste": 0.1}
    inputs1 = MockInputs("mixed", "motorcycle")
    run_test("Student in India", user1, assessment1, inputs1)
    
    # Scenario 2: Adult in Berlin, Germany — car user, non-vegetarian
    user2 = MockUser("adult", "Germany")
    assessment2 = {"total_emission": 14.5, "transport": 6.0, "energy": 4.0, "food": 3.5, "waste": 1.0}
    inputs2 = MockInputs("non_vegetarian", "car")
    run_test("Adult in Germany", user2, assessment2, inputs2)
    
    # Scenario 3: Elderly in California, US — low travel, high home energy use
    user3 = MockUser("senior", "United States")
    assessment3 = {"total_emission": 18.0, "transport": 1.0, "energy": 12.0, "food": 4.0, "waste": 1.0}
    inputs3 = MockInputs("mixed", "car")
    run_test("Elderly in California", user3, assessment3, inputs3)
