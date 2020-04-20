from ..db import Base, Session

from sqlalchemy import Column, Integer, String, Date, desc
from sqlalchemy.sql import func

from datetime import date

class TimeEntry(Base):
    __tablename__ = "timeentries"   

    id = Column(Integer, primary_key=True)
    discord_id = Column(Integer)
    guild_id = Column(Integer)
    channel_id = Column(Integer)
    resolution = Column(Integer)
    amount = Column(Integer)
    day = Column(Date)

    def __repr__(self):
        return "TimeEntry(id={}, discord_id={}, guild_id={}, channel_id={}, resolution={}, amount={}, day={})"\
                .format(self.id, self.discord_id, self.guild_id, self.channel_id, self.resolution, self.amount, self.day)

    @classmethod
    def get_summary(cls, guild_id):
        session = Session()

        today = date.today()
        res = session.query(TimeEntry.discord_id,
                            func.sum(TimeEntry.amount * TimeEntry.resolution).label("total_time"),
                            )\
                            .filter_by(guild_id=guild_id)\
                            .filter_by(day=today)\
                            .group_by(TimeEntry.discord_id)\
                            .order_by(desc("total_time"))\
                            .all()
        return res

    @classmethod
    def update_user(cls, user_id, channel_id, guild_id, resolution):
        session = Session()
        entry = session.query(TimeEntry)\
            .filter_by(discord_id=user_id, guild_id=guild_id, channel_id=channel_id, day=date.today())\
            .first()
        if entry is None:
            entry = TimeEntry(
                discord_id=user_id,
                guild_id=guild_id,
                channel_id=channel_id,
                day=date.today(), 
                resolution=resolution,
                amount=1
            )
            session.add(entry)
        else:
            entry.amount += 1
        session.commit()

Base.metadata.create_all()
