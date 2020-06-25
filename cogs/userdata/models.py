from ..db import Base, Session
from sqlalchemy import Column, Integer, String


class DiscordUser(Base):
    __tablename__ = "userdata"

    discord_id = Column(Integer, primary_key=True)
    nick = Column(String)

    @classmethod
    def add_user(cls, username, discord_id):
        session = Session()

        user = session.query(DiscordUser).filter_by(discord_id=discord_id).first()
        if user is not None:
            session.close()
            return

        user = DiscordUser(discord_id=discord_id, nick=username)
        session.add(user)

        session.commit()


Base.metadata.create_all()
