"""Run the Clipster application agent and print diagnostic logs."""
from user_management.models import User
from cv_management.models import CV, PersonalInfo
from job_sourcing.models import JobOffer
from matching.models import Match
from notifications.models import Notification
from applications.models import Application, ApplicationStatus
from shared.database import SessionLocal
from applications.adapters.playwright_application_channel import PlaywrightApplicationChannel
from applications.application_service import ApplicationService
import uuid

db = SessionLocal()
app_id = uuid.UUID('4b383854-3c74-4c87-856f-f4c591a1ef57')
app = db.get(Application, app_id)
app.status = ApplicationStatus.APPROVED
app.failure_reason = None
db.commit()
print('Running agent v3...')
channel = PlaywrightApplicationChannel()
result = ApplicationService.run_agent(app.id, app.user_id, channel, db)
print(f'Status: {result.status}')
print(f'Failure: {result.failure_reason}')
print('--- FILL LOGS ---')
for log in (result.execution_logs or []):
    step = log.get('step', '')
    if 'FILL_GEM' in step or 'SUBMIT' in step or '6_' in step or '5_' in step:
        msg = log.get('message', '')
        st = log.get('status', '')
        print(f'  [{step}] ({st}) {msg}')
