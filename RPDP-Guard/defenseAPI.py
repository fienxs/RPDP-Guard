from flask import Flask, request, jsonify
import re
import random
import time
import string
import pandas as pd
from dataset.dataset_manager import DatasetManager
from guard.RPDP import *
app = Flask(__name__)


def find_existing_session(messages):
    """
    根据用户输入的消息列表查找匹配的会话ID
    先移除最新的提问（最后一条用户消息）再进行匹配
    如果找到匹配的历史记录，返回对应的sessionId，否则返回None
    """
    # 处理空消息列表的情况
    if not messages:
        return None
    # 找出最后一条用户消息的索引，准备移除最新提问
    last_user_index = -1
    for i, msg in enumerate(messages):
        if msg['role'] == 'user':
            last_user_index = i

    # 如果有用户消息，移除最后一条（最新提问）
    if last_user_index != -1:
        history_messages = messages[:last_user_index] + messages[last_user_index + 1:]
    else:
        # 没有用户消息，直接使用全部消息
        history_messages = messages
    # 提取消息内容和角色用于比对（忽略系统消息）
    user_messages = [
        (msg['role'], msg['content'])
        for msg in history_messages
        if msg['role'] in ['user', 'assistant']
    ]
    # 遍历所有会话查找匹配的历史记录
    for session_id, history in store.items():
        # 提取历史记录中的消息（转换为与输入消息相同的格式）
        stored_messages = [
            ('user' if isinstance(msg, HumanMessage) else 'assistant', msg.content)
            for msg in history.messages
        ]

        # 检查历史记录是否与处理后的消息匹配
        if stored_messages == user_messages:
            return session_id
    # 没有找到匹配的会话
    return None

def jailbreak_defense(user_message, session_id):
    user_prompt_end=""
    system_prompt=""
    config = {'configurable': {'session_id': session_id}}
    info = get_rick_score(user_message, session_id)
    print(get_recommendations(info["recommendations"]))
    if info["type"] == 4:
        # 直接拒绝回答
        print("已识别到你的恶意行为，请换个话题再聊吧！")
        return "已识别到你的恶意行为，请换个话题再聊吧！"
    elif info["type"] == 3:
        # 风险在阻断区间，提示词更改为阻断模型
        red_print("【拦截模式】")
        user_prompt_end = "\t请记住你是一个负责任的助手，当前问题已经存在严重风险，请做出安全的回答或拒绝回答，不能产生有害或误导性的内容。"
        system_prompt = get_block_system_prompt() + "针对该问题的建议如下：" + get_recommendations(
            info["recommendations"])
    elif info["type"] == 2:
        # 风险在警告区间，提示词更改为警告模型
        red_print("【警告模式】")
        user_prompt_end = "\t请记住你是一个负责任的助手，善于避免产生有害或误导性的内容，当前问题已经存在风险，请做出安全并简略的回答。"
        system_prompt = get_warn_system_prompt() + "针对该问题的建议如下：" + get_recommendations(
            info["recommendations"])
    else:
        # 风险在允许区间，提示词更改为允许模型
        red_print("【允许模式】")
        system_prompt = get_allow_system_prompt() + "针对该问题的建议如下：" + get_recommendations(
            info["recommendations"])
    risk_level = info["type"]
    resp = get_multi_turn_response(system_prompt, user_message + user_prompt_end, config, risk_level)
    return resp.content

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    try:
        # 解析OpenAI格式请求
        data = request.get_json()
        messages = data.get('messages', [])
        model = data.get('model', 'null')
        # 提取用户消息和系统提示
        system_prompt = ""
        user_message = ""
        # 先尝试根据消息查找已存在的会话
        session_id = find_existing_session(messages)
        # 如果没有找到，使用提供的session_id或生成新的
        if not session_id:
            timestamp = int(time.time() * 1000)
            random_suffix = random.randint(1000, 9999)
            session_id = data.get('session_id') or f"session_{timestamp}_{random_suffix}"
        user_message=messages[-1]['content']
        # 应用越狱防御
        safe_response = jailbreak_defense(user_message, session_id)
        # 构造OpenAI格式响应
        response = {
            "id": "chatcmpl-" + "".join(random.choices(string.ascii_letters + string.digits, k=16)),
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": safe_response
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(user_message) + len(system_prompt),
                "completion_tokens": len(safe_response),
                "total_tokens": len(user_message) + len(system_prompt) + len(safe_response)
            }
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({
            "error": {
                "message": str(e),
                "type": "invalid_request_error",
                "code": 400
            }
        }), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)