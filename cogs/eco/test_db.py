import pytest
from . import User, Bet, BetEntry, Session


def test_single_bet():
    session = Session()

    u1 = User(nick="roman", discord_id=0, guild_id=0, money=1000)
    u2 = User(nick="ryszard", discord_id=1, guild_id=0, money=1000)
    session.add_all([u1, u2])

    b1 = u1.create_bet(session, "test bet")
    u1.enter_bet(session, b1, 100, True)
    u2.enter_bet(session, b1, 300, False)

    b1.resolve(session, True)

    a1 = session.query(User).all()
    a2 = session.query(Bet).all()
    a3 = session.query(BetEntry).all()

    print("\n".join(map(str, a1)))
    print("===============")
    print("\n".join(map(str, a2)))
    print("===============")
    print("\n".join(map(str, a3)))



    assert u1.money == 1300
    assert u2.money == 700

    # session.commit()


def test_two_bets():
    session = Session()

    u1 = User(nick="roman", discord_id=0, guild_id=0, money=1000)
    u2 = User(nick="ryszard", discord_id=1, guild_id=0, money=1000)
    session.add_all([u1, u2])

    b1 = u1.create_bet(session, "test bet")
    b2 = u2.create_bet(session, "test bet no. 2")

    u1.enter_bet(session, b1, 100, True)
    u1.enter_bet(session, b2, 500, False)

    u2.enter_bet(session, b2, 200, True)
    u2.enter_bet(session, b1, 300, False)

    b1.resolve(session, True)
    b2.resolve(session, True)

    assert u1.money == 800
    assert u2.money == 1200
