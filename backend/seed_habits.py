import uuid
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.habit_definition import HabitDefinition

def seed_habit_definitions():
    db: Session = SessionLocal()
    try:
        definitions = [
            {"habit_type": "public_transport", "factor": 1.2, "unit": "kg CO2e"},
            {"habit_type": "recycling", "factor": 0.5, "unit": "kg CO2e"},
            {"habit_type": "save_electricity", "factor": 0.8, "unit": "kg CO2e"},
            {"habit_type": "water_conservation", "factor": 0.3, "unit": "kg CO2e"},
            {"habit_type": "plastic_reduction", "factor": 0.4, "unit": "kg CO2e"},
        ]

        for d in definitions:
            existing = db.query(HabitDefinition).filter(HabitDefinition.habit_type == d["habit_type"]).first()
            if not existing:
                new_def = HabitDefinition(
                    habit_type=d["habit_type"],
                    carbon_saving_factor=d["factor"],
                    unit=d["unit"]
                )
                db.add(new_def)
                
        db.commit()
        print("Habit definitions seeded successfully.")
    except Exception as e:
        print(f"Error seeding habit definitions: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_habit_definitions()
