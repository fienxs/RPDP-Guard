def get_allow_system_prompt()-> str:
    return ""
def get_warn_system_prompt()->str:
    return ""
def get_block_system_prompt()->str:
    return ""
#评分提示词
def get_prompt_for_evaluator_score(goal: str) -> str:

    return f"""

    """
def get_single_prompt(current_issues)->str:
    return f"""

    """


def get_multi_turn_prompt(current_issues):
    return f"""

"""




