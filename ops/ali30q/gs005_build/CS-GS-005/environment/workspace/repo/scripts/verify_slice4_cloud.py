"""Inc 2 Slice 4 cloud verification · on_agent_register + update_progression_gates."""
import os
import sys
sys.path.insert(0, ".")
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

engine = create_engine(os.environ["DATABASE_URL"])
db = sessionmaker(bind=engine)()

from services.inc2_settlement import on_agent_register, update_progression_gates

test_aid = 9000002  # V5 existing

# cleanup prior runs
db.execute(
    text("DELETE FROM onboarding_rewards WHERE beneficiary_agent = :a AND stage = :s"),
    {"a": str(test_aid), "s": "inc2_wel"},
)
db.execute(
    text("UPDATE agents SET correct_votes_count = 0, proposing_unlocked = FALSE, voter_bounty_unlocked = FALSE WHERE id = :a"),
    {"a": test_aid},
)
db.commit()

print("=== onboarding call 1 ===")
print(on_agent_register(db, test_aid))
print("=== onboarding call 2 (idempotent) ===")
print(on_agent_register(db, test_aid))

print("=== progression: 4 correct votes ===")
for i in range(4):
    r = update_progression_gates(db, test_aid, was_correct=True)
    print(f" vote {i+1}: count={r.get('correct_votes_count')} prop={r.get('proposing_unlocked')} vbf={r.get('voter_bounty_unlocked')}")

row = db.execute(
    text("SELECT correct_votes_count, proposing_unlocked, voter_bounty_unlocked FROM agents WHERE id = :a"),
    {"a": test_aid},
).fetchone()
print(f"FINAL agents row: count={row[0]} proposing_unlocked={row[1]} voter_bounty_unlocked={row[2]}")

ob = db.execute(
    text("SELECT reward_id, stage, beneficiary_agent, amount_nau FROM onboarding_rewards WHERE beneficiary_agent = :a AND stage = :s"),
    {"a": str(test_aid), "s": "inc2_wel"},
).fetchone()
print(f"onboarding row: id={ob[0]} stage={ob[1]} beneficiary={ob[2]} amount={ob[3]}")
