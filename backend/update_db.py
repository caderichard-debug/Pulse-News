# update_user_name.py
from app.database import engine
from sqlmodel import Session, select
from app.models import User

with Session(engine) as session:
    user = session.exec(select(User).where(User.email == 'cade.richard@gmail.com')).first()
    if user:
        user.name = 'Cade Richard'
        session.add(user)
        session.commit()
        print('Updated:', user.name)
    else:
        print('User not found')
        