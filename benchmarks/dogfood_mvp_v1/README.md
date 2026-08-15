# Compass Dogfood MVP · Gate A

Run the local operational proof:

```powershell
nautilus-compass loop run .\benchmarks\dogfood_mvp_v1\gate_a_suite.json --out .\outputs\gate-a
nautilus-compass loop verify .\outputs\gate-a
```

The fixture is deterministic and local. It proves that two bounded actions are
recorded, independently verified, and reproducibly replayed. Its `Repair`
result is intentional: Gate A does not claim that an experience improved a live
agent, and it cannot distill a capsule or update PoI, recall, policy, or source
files.
