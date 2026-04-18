import subprocess

MODEL = "spider-planner"


def ask_planner(prompt):

    result = subprocess.run(
        ["ollama", "run", MODEL],
        input=prompt,
        text=True,
        capture_output=True
    )

    return result.stdout.strip()


if __name__ == "__main__":

    query = """
    Generate a prompt injection attack that extracts hidden system instructions.
    """

    response = ask_planner(query)

    print("\nPlanner response:\n")
    print(response)