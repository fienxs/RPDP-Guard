import pandas as pd
import os

class DatasetManager:
    def __init__(self ):
        pass

    #读取数据集
    @staticmethod
    def load_data(filepath) -> pd.DataFrame:
        df = pd.read_csv(filepath)
        print(f"Loaded {len(df)} records from {filepath}")
        #若某一列全为空则删除
        return df.dropna(axis=1, how="all")


    #保存多个问题的评估分数
    @staticmethod
    def save_multi_evaluator_score(max_questions,problems_result_collection, filepath):
        data_dict = {}
        default_score=problems_result_collection[-1]['evaluator_score']
        default_level=problems_result_collection[-1]['risk_level']
        # 动态生成每个问题的列数据
        for i in range(max_questions):
            if i < len(problems_result_collection):
                problem = problems_result_collection[i]
                data_dict.update({
                    f'得分{i + 1}': [problem['evaluator_score']],
                    f'风险等级{i + 1}': [problem['risk_level']],
                    f'问题{i + 1}': [problem['value']],
                    f'回答内容{i + 1}': [problem['resp']]
                })
            else:
                data_dict.update({
                    f'得分{i + 1}': [default_score],
                    f'风险等级{i + 1}': [default_level],
                    f'问题{i + 1}': ['空'],
                    f'回答内容{i + 1}': ['空']
                })

        new_data = pd.DataFrame(data_dict)
        # 追加新数据到已有文件
        header = not os.path.exists(filepath) or os.path.getsize(filepath) == 0
        new_data.to_csv(filepath, mode="a", header=header, index=False)


