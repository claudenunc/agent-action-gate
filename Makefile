.PHONY: test demo demo-full demo-langgraph demo-crewai demos verify

test:
	python -m unittest discover tests -v

demo:
	python examples/demo_blocked_exfiltration.py

demo-full:
	python examples/full_runtime_demo.py

demo-langgraph:
	python examples/langgraph_integration.py

demo-crewai:
	python examples/crewai_integration.py

demos: demo demo-full demo-langgraph demo-crewai

verify:
	python scripts/action_gate.py verify-log
