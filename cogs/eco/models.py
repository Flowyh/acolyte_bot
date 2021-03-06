from __future__ import annotations


import sqlalchemy
import random
from sqlalchemy import Column, Integer, String, ForeignKey, Float, Boolean, func
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from cogs.db import Base, Session
import dotenv
import os


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    nick = Column(String)
    discord_id = Column(Integer)
    guild_id = Column(Integer)
    money = Column(Float)


    def __repr__(self):
        return f"User(id={self.id}, nick={self.nick}, discord_id={self.discord_id}, money={self.money})"

    def transfer(self, amount: int, to: User):
        self.money -= amount
        to.money += amount

    def create_bet(self, session, description):
        bet = Bet(creator=self, description=description, active=True)

        session.add(bet)
        return bet

    def enter_bet(self, session, bet, amount, on):
        bet.enter_user(session, self, amount, on)


class Bet(Base):
    __tablename__ = "bets"

    # bets should be guild-dependant, but that's achieved via having different
    # User entries for discord users on different guilds

    id = Column(Integer, primary_key=True)
    creator_id =  Column(Integer, ForeignKey('users.id'), nullable=False)
    description = Column(String, nullable=False)
    active = Column(Boolean, nullable=False)
    
    creator = relationship("User", back_populates="bets")

    def enter_user(self, session, user, amount, on):
        min_money = user.money - sum((e.amount for e in user.bet_entries if e.bet.active))
        if amount > min_money:
            raise ValueError("Not enough money")
            
        be = BetEntry(user=user, bet=self, on=on, amount=amount)
        session.add(be)

    def leave_user(self, session, user):
        a = session.query(BetEntry).all()
        print("\n".join(map(str, a)))
        be = session.query(BetEntry)\
                .filter_by(bet_id=self.id)\
                .filter_by(user_id=user.id)\
                .first()
        if be is None:
            raise ValueError("User is not in this Bet")
        session.delete(be)

        # mark Bet and User as out of date - this will effectively remove the BetEntry from all instances
        session.expire(self)  
        session.expire(user)

    def resolve(self, session, result):

        for_pool = sum((e.amount for e in self.entries if e.on))
        against_pool = sum((e.amount for e in self.entries if not e.on))

        print("for", for_pool)
        print("against", against_pool)

        total_pool = for_pool + against_pool

        print("total_entries", session.query(BetEntry).count())

        bet_stakes = session.query(User, BetEntry.amount / for_pool * total_pool, BetEntry.amount / against_pool * total_pool, BetEntry.amount, BetEntry.on).join(BetEntry).filter(BetEntry.bet_id == self.id)


        print("\n".join(map(str, bet_stakes)))

        for user, for_win, against_win, loss, on in bet_stakes:
            user.money -= loss
            if result and on:
                user.money += for_win
            elif not result and not on:
                user.money +=  against_win

        self.active = False

    def __repr__(self):
        return f"Bet(creator={self.creator}, description='{self.description}', active={self.active})"




User.bets = relationship("Bet", order_by=Bet.id, back_populates="creator")


class BetEntry(Base):
    __tablename__ = "bet_entries"

    id = Column(Integer, primary_key=True)
    bet_id = Column(Integer, ForeignKey("bets.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    on = Column(Boolean)
    amount = Column(Float)

    bet = relationship("Bet", back_populates="entries")
    user = relationship("User", back_populates="bet_entries")

    def __repr__(self):
        return f"BetEntry(bet={self.bet}, user={self.user}, on={self.on}, amount={self.amount})"


User.bet_entries = relationship("BetEntry", order_by=BetEntry.id, back_populates="user")
Bet.entries = relationship("BetEntry", order_by=BetEntry.id, back_populates="bet")


Base.metadata.create_all()


if __name__ == "__main__":
    session = Session()

    u1 = User(nick="roman", discord_id=0, guild_id=0, money=1000)
    b1 = u1.create_bet(session, "AAAAAAAAAAAAAAAAAAAaa", 100)

    u2 = User(nick="ryszard", discord_id=1, guild_id=0, money=1000)
    u2.enter_bet(session, b1, 300, False)

    u3 = User(nick="zenon", discord_id=2, guild_id=0, money=1000)
    u3.enter_bet(session, b1, 200, False)

    print(u1.bet_entries)
    b1.resolve(session, False)

    a1 = session.query(User).all()
    # a2 = session.query(Bet).all()
    # a3 = session.query(BetEntry).all()

    print("===============")
    print("\n".join(map(str, a1)))
    # print(a2)
    # print(a3)


    # session.close()
