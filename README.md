## An interface for requirement-driven prompting

This is a research prototype to facilitate requirement-driven prompting. Instead of writing prompts, users are encourage to write down high-level requirements, grounded in data observations.
The requirements will then be compiled into a prompt for iterative development.

We build the prototype on the top of [Zeno](https://github.com/zeno-ml/zeno) to leverage its support for interactive evaluation.

For development, check [DEVELOPMENT.md](DEVELOPMENT.md)

For local deployment, use `sudo docker compose up --build`, with pre-configured OPENAI_API_KEY and proper ports
