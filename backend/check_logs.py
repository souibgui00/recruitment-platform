import uuid
from shared.database import SessionLocal
from applications.models import Application

db = SessionLocal()
app_id = uuid.UUID('4b383854-3c74-4c87-856f-f4c591a1ef57')
app = db.get(Application, app_id)

print(f"Status: {app.status}")
print(f"Failure: {app.failure_reason}")
print("--- LOGS ---")
if app.execution_logs:
    for log in app.execution_logs:
        print(f"[{log.get('step')}] ({log.get('status')}) {log.get('message')}")
else:
    print("No logs found.")
