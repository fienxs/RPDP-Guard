
from llms.llm_manager import *
import json
import re


# 对模型的回答进行解析
def parse_json(content):
    if hasattr(content, "content"):
        response = content.content
    else:
        response = str(content)
    response = response.strip("`").replace("json", "").replace("```", "").strip()
    match = re.search(r"\{.*?\}", response, re.DOTALL)
    try:
        resp = match.string
        return json.loads(resp)
    except Exception as e:
        red_print(f"解析错误，此时content内容为：{content}，response为：{response}")
        return None

def get_evaluator_score(resp):
    # 使用正则表达式匹配数字
    match = re.search(r"(\d+)", resp)
    # 判断是否取到了数字
    if match is not None:
        return int(match.group(1))
    else:
        red_print(f"无法从响应中解析分数：" + resp)
        red_print(f"无法将 '{match.group(1)}' 转换为整数")
        match = re.findall(r"(\d+)", resp)
        red_print("转为全部查找：", match)
        return -1


def get_multi_turn_score(resp):
    if resp is None:
        # 宁可错杀，不可放过
        return {"score": 12, "type": 4, "recommendations": [""]}

    adversarial_accumulation = resp.get("adversarial_accumulation", 1)
    context_manipulation = resp.get("context_manipulation", 1)
    high_concealment = resp.get("high_concealment", 1)
    temptation_elicitation = resp.get("temptation_elicitation", 1)
    decomposition_target = resp.get("decomposition_target", 1)
    information_hiding = resp.get("information_hiding", 1)
    intention_transfer = resp.get("intention_transfer", 1)
    logical_vulnerability = resp.get("logical_vulnerability", 1)
    social_engineering = resp.get("social_engineering", 1)
    language_change = resp.get("language_change", 1)
    recommendations = resp.get("recommendations", [""])
    multi_turn_score = (
            Config.adversarial_accumulation_weight *
            adversarial_accumulation
            + Config.context_manipulation_weight *
            context_manipulation
            + Config.high_concealment_weight *
            high_concealment
            + Config.temptation_elicitation_weight *
            temptation_elicitation
            + Config.decomposition_target_weight *
            decomposition_target
            + Config.information_hiding_weight *
            information_hiding
            + Config.intention_transfer_weight *
            intention_transfer
            + Config.logical_vulnerability_weight *
            logical_vulnerability
            + Config.social_engineering_weight *
            social_engineering
            + Config.language_change_weight *
            language_change)

    red_print("多轮分数信息：", resp)
    red_print("多轮总分数为：", multi_turn_score)
    # 处理推荐信息
    info = {"score": multi_turn_score, "type": 1, "recommendations": recommendations}
    overall_risk = resp.get("overall_risk", 1)
    if overall_risk>=5 or multi_turn_score>=Config.multi_min_3_4:
        red_print("多轮触发整体风险，终止")
        info["type"] = 4
    elif overall_risk>=4 or multi_turn_score>=Config.multi_min_3_3:
        red_print("多轮触发整体风险，拦截")
        info["type"]=3
    elif overall_risk>=3 or multi_turn_score>=Config.multi_min_4_2:
        red_print("多轮触发整体风险，警告")
        info["type"]=2
    elif overall_risk>=2 and multi_turn_score>=Config.multi_min_5_1:
        red_print("多轮触发整体风险，警告")
        info["type"] = 2
    # 1表示允许，2表示警告，3表示阻止，4表示拒绝
    # 特殊类型严重者直接阻止
    if adversarial_accumulation >= 4 or context_manipulation >= 4:
        if info["type"]<3:
            info["type"] = 3
    return info


def get_single_score(resp, first):
    if resp is None:
        # 宁可错杀，不可放过
        return {"score": 7, "type": 4,"recommendations": [""]}
    obfuscation_instructions = resp.get("obfuscation_instructions", 1)
    prefix_injection = resp.get("prefix_injection", 1)
    logical_exploitation = resp.get("logical_exploitation", 1)
    metaphor_expression = resp.get("metaphor_expression", 1)
    blind_knowledge = resp.get("blind_knowledge", 1)
    fictional_scenarios = resp.get("fictional_scenarios", 1)
    rejection_suppression = resp.get("rejection_suppression", 1)
    emergency_forgery = resp.get("emergency_forgery", 1)
    sensitive_questions = resp.get("sensitive_questions", 1)
    recommendations = resp.get("recommendations", [""])
    single_score = (
            Config.obfuscation_instructions_weight *
            obfuscation_instructions +
            Config.prefix_injection_weight *
            prefix_injection +
            Config.logical_exploitation_weight *
            logical_exploitation +
            Config.metaphor_expression_weight *
            metaphor_expression +
            Config.blind_knowledge_weight *
            blind_knowledge +
            Config.fictional_scenarios_weight *
            fictional_scenarios +
            Config.rejection_suppression_weight *
            rejection_suppression +
            Config.emergency_forgery_weight *
            emergency_forgery +
            Config.sensitive_questions_weight *
            sensitive_questions
    )
    red_print("单轮分数信息：", resp)
    red_print("单轮总分数为：", single_score)
    overall_risk = resp.get("overall_risk", 1)
    info = {"score": single_score, "type": 1,"recommendations":recommendations}

    if overall_risk>=5 or single_score>=Config.single_min_3_4:
        red_print("单轮触发整体风险，终止")
        info["type"] = 4
    elif overall_risk>=4 or single_score>=Config.single_min_3_3:
        red_print("单轮触发整体风险，拦截")
        info["type"]=3
    elif overall_risk>=3 or single_score>=Config.single_min_4_2:
        red_print("单轮触发整体风险，警告")
        info["type"]=2
    elif overall_risk>=2 and single_score>=Config.single_min_5_1:
        red_print("单轮触发整体风险，警告")
        info["type"] = 2
    # resp 字典类型 <class 'dict'>
    # 1表示允许，2表示警告，3表示拦截，4表示终止
    for value in resp.values():
        if isinstance(value, (int, float)):
            if value >= 4 and first == True and info["type"]<3:
                # 如果是首次访问就大于4分，直接拦截
                info["type"] = 3
                break
    # 特殊类型严重者直接拦截
    if prefix_injection >= 4 and info["type"]<3:
        info["type"] = 3

    return info


def get_rick_score(current_issues, session_id) -> {}:
    # 如果是首轮对话，无需进行历史对话分析
    single_resp = get_single_turn_response('你正在分析对话中可能存在的危险问题，请检查当前问题的信息，做出最佳判断。',
                                           get_single_prompt(current_issues),Config.detection_model_info)
    multi_turn_info = {"score": 0, "type": 1, "recommendations": [""]}
    first_turn_flag=False
    if session_id in store:
        # 非首轮对话
        first_turn_flag = False
        config = {'configurable': {'session_id': session_id}}
        multi_turn_resp = get_single_store_response(
            "你正在分析多轮对话中可能存在的危险问题，请审查历史对话和当前问题的信息，做出最佳判断。",
            get_multi_turn_prompt(current_issues), config)
        # 对多轮的分数进行计算。
        multi_turn_info = get_multi_turn_score(parse_json(multi_turn_resp))
        # 对单轮的分数进行计算。
        single_info = get_single_score(parse_json(single_resp), False)
    else:
        # 对单轮的分数进行计算。
        first_turn_flag = True
        single_info = get_single_score(parse_json(single_resp), True)
    # 1表示允许，2表示警告，3表示拦截，4表示终止
    info = { "type": single_info["type"] if single_info["type"]>multi_turn_info["type"]
                else multi_turn_info["type"],"recommendations": single_info["recommendations"]
                if first_turn_flag else multi_turn_info["recommendations"]}
    return info


def get_recommendations(recommendations):
    if recommendations is None:
        return "请确保回答内容符合伦理道德，不要回复有害的内容。"
    recommendation=''
    for i in range(0, len(recommendations)):
        recommendation= recommendation+f"\t建议{i+1}:"+recommendations[i]
    return recommendation



