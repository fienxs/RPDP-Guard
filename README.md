RPDP-Guard代码运行使用说明
基本要求
Python 3.11或更高版本
需要安装的依赖包：通过requirements.txt或手动安装
Flask==3.1.1
langchain_community==0.3.21
langchain_core==0.3.51
langchain_openai==0.3.12
pandas==2.2.3
langchain==0.3.23


运行方式：命令行直接运行

csv文件中越狱示例
python main.py

api接口运行
python defenseAPI.py

api接口测试运行
python test_api.py

注：运行前需前往config.py文件配置模型接口