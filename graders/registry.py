
def grade(history, task):
    for h in history:
        if h["action_type"] == "take_action":
            if h["payload"].get("fix") == task["solution"]:
                return 1.0
    return 0.0
