.PHONY: test demo

test:
	python -m unittest discover tests -v

demo:
	python examples/demo_blocked_exfiltration.py
