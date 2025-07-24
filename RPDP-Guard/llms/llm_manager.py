import copy

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from config.config import *
from langchain_core.messages import HumanMessage, AIMessage
from prompts.prompts import *
from langchain_core.output_parsers import StrOutputParser

#红色输出
def red_print(*args, sep=' ', end=' '):
    output = sep.join(map(str, args)) + end
    print(f"{Config.RED}{output}{Config.RESET}")


#选择模型函数
def choose_model(model_info,risk_info):
    return ChatOpenAI(
    model=model_info['model'],
    temperature=risk_info['temperature'],
    api_key=model_info['key'],
    base_url=model_info['url'],
    top_p=risk_info['top_p'],
)
#----------此处开始为多轮询问处理--------------------
#保存聊天的历史记录
#所有用户的记录都保存在store，key:sessionId
store={}

#接受一个sessionId返回一个消息历史记录对象
def get_session_history(session_id:str):
    if session_id not in store:
        store[session_id]=ChatMessageHistory()
    return store[session_id]

def get_multi_turn_response(system_prompt,content,config,risk_level):
    multi_turn_prompt_template = ChatPromptTemplate.from_messages([
        ('system', '{system_prompt}'),
        MessagesPlaceholder(variable_name='msg')
    ])
    if risk_level==1:
        risk_info=Config.allow_model_info
    elif risk_level==2:
        risk_info=Config.warn_model_info
    else :
        risk_info=Config.interception_model_info

    multi_turn_chain = multi_turn_prompt_template | choose_model(Config.target_model_info,risk_info)
    multi_turn_do_message = RunnableWithMessageHistory(
        multi_turn_chain,
        get_session_history,
        # 每次聊天的时候发送msg的key
        input_messages_key='msg'
    )
    try:
        resp=multi_turn_do_message.invoke(
                {'msg':[HumanMessage(content=content)],
                 'system_prompt':system_prompt},
                config=config
            )
        return resp
    except Exception as e:
        red_print(e)
        return "模型出现错误，拒绝响应"

#----------多轮话题处理结束--------------------


#------风险评判专用----------------------
single_store={}
def get_single_store_history(session_id:str):
    single_store[session_id]=copy.deepcopy(get_session_history(session_id))
    return single_store[session_id]

def get_single_store_response(system_prompt,content,config):
    multi_turn_prompt_template = ChatPromptTemplate.from_messages([
        ('system', '{system_prompt}'),
        MessagesPlaceholder(variable_name='msg')
    ])
    multi_turn_chain = multi_turn_prompt_template | choose_model(Config.detection_model_info,Config.judge_model_info)
    multi_turn_do_message = RunnableWithMessageHistory(
        multi_turn_chain,
        get_single_store_history,
        # 每次聊天的时候发送msg的key
        input_messages_key='msg'
    )
    try:
        resp=multi_turn_do_message.invoke(
                {'msg':[HumanMessage(content=content)],
                 'system_prompt':system_prompt},
                config=config
            )
        return resp
    except Exception as e:
        red_print(e)
        return "模型出现错误，拒绝响应"



#----------此处开始为单次询问处理--------------------
def get_single_turn_response(system_prompt,content,model_info):
    single_turn_prompt_template = ChatPromptTemplate.from_messages([
        ('system', system_prompt),
        ('user', "{text}")
    ])
    single_turn_parser = StrOutputParser()
    single_turn_chain = single_turn_prompt_template | choose_model(model_info,Config.judge_model_info) | single_turn_parser
    try:
        resp = single_turn_chain.invoke({'text': content})
        return resp
    except Exception as e:
        red_print(e)
        return "模型出现错误，拒绝响应"


#----------单轮话题处理结束--------------------
