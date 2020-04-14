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


def test_no_money():
    session = Session()

    u1 = User(nick="roman", discord_id=0, guild_id=0, money=1000)
    u2 = User(nick="ryszard", discord_id=1, guild_id=0, money=1000)
    session.add_all([u1, u2])

    b1 = u1.create_bet(session, "test bet")
    u1.enter_bet(session, b1, 100, True)
    with pytest.raises(ValueError):
        u2.enter_bet(session, b1, 9999999, False)

    b1.resolve(session, True)

    assert u1.money == 1000
    assert u2.money == 1000


def test_two_bets_no_money():
    session = Session()

    u1 = User(nick="roman", discord_id=0, guild_id=0, money=1000)
    u2 = User(nick="ryszard", discord_id=1, guild_id=0, money=1000)
    session.add_all([u1, u2])

    b1 = u1.create_bet(session, "test bet")
    b2 = u2.create_bet(session, "test bet no. 2")

    u1.enter_bet(session, b1, 100, True)
    u1.enter_bet(session, b2, 900, False)

    u2.enter_bet(session, b2, 200, True)

    with pytest.raises(ValueError):
        u2.enter_bet(session, b1, 900, False)

    b1.resolve(session, True)
    b2.resolve(session, True)

    assert u1.money == 100
    assert u2.money == 1900


def test_single_better_lost():
    session = Session()

    u1 = User(nick="roman", discord_id=0, guild_id=0, money=1000)
    session.add_all([u1])

    b1 = u1.create_bet(session, "test bet")

    b1.enter_user(session, u1, 500, False)
    b1.resolve(session, True)

    assert u1.money == 500


def test_past_bets_limiting_money():
    session = Session()

    u1 = User(nick="roman", discord_id=0, guild_id=0, money=1000)
    session.add_all([u1])

    b1 = u1.create_bet(session, "test bet")

    b1.enter_user(session, u1, 1000, True)
    b1.resolve(session, True)

    assert u1.money == 1000

    b2 = u1.create_bet(session, "second bet")
    b2.enter_user(session, u1, 200, True)

    b2.resolve(session, True)
    
    assert u1.money == 1000


def test_leave_bet():

    session = Session()

    u1 = User(nick="roman", discord_id=0, guild_id=0, money=1000)
    u2 = User(nick="ryszard", discord_id=1, guild_id=0, money=1000)
    session.add_all([u1, u2])

    b1 = u1.create_bet(session, "test bet")
    u1.enter_bet(session, b1, 100, True)
    u2.enter_bet(session, b1, 300, False)

    b2 = u1.create_bet(session, "test bet2")
    u1.enter_bet(session, b2, 500, False)
    u2.enter_bet(session, b2, 500, True)

    b2.leave_user(session, u1)
    
    b1.resolve(session, True)

    assert u1.money == 1300
    assert u2.money == 700

    b2.resolve(session, True)

    assert u1.money == 1300
    assert u2.money == 700



