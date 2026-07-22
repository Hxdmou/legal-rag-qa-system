# NLP 新闻分类作业 - RNN 模型

## 项目简介

本项目使用 RNN（循环神经网络）模型完成新闻文本分类任务，使用 AG News 数据集。

## 环境要求

- Python 3.7+
- PyTorch 1.9.0+
- torchtext 0.10.0+

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行方式

### 1. 训练模型

```bash
python train.py
```

### 2. 项目结构

```
nlp_news_classification/
├── data_preprocessing.py    # 数据预处理模块
├── rnn_model.py             # RNN模型定义
├── train.py                 # 训练和测试主程序
├── requirements.txt         # 依赖包列表
├── README.md                # 说明文档
├── data/                    # 数据目录
├── models/                  # 模型保存目录
└── results/                 # 结果保存目录
```

## 模型结构

### RNN 模型架构

- **嵌入层**: 将词索引转换为词向量
- **LSTM 层**: 2层LSTM，隐藏维度256
- **全连接层**: 2层全连接，包含ReLU激活和Dropout
- **输出层**: 4个类别（World, Sports, Business, Sci/Tech）

### 超参数

- 词汇表大小: 约20,000+
- 词嵌入维度: 128
- LSTM隐藏维度: 256
- LSTM层数: 2
- Dropout: 0.3
- 批次大小: 64
- 训练轮数: 5
- 学习率: 0.001
- 最大序列长度: 128

## 数据集

### AG News 数据集

- **训练集**: 120,000条新闻
- **测试集**: 7,600条新闻
- **类别数**: 4类
  - 1: World
  - 2: Sports
  - 3: Business
  - 4: Sci/Tech

## 实验结果

训练完成后，结果将保存在：
- 模型: `models/rnn_best_model.pth`
- 训练日志: `results/training_results.txt`

### 预期性能

- 训练准确率: 约 85-90%
- 测试准确率: 约 85-90%

## 功能模块

### 1. data_preprocessing.py
- 文本清洗（小写化、去除标点）
- 构建词汇表
- 数据集封装
- 数据批处理

### 2. rnn_model.py
- LSTM模型定义
- 前向传播实现

### 3. train.py
- 模型训练循环
- 模型评估
- 结果保存
- 最佳模型选择

## 输出说明

训练过程中会显示：
- 每个批次的损失
- 每个epoch的训练/测试损失和准确率
- 最佳模型自动保存

结果文件包含：
- 超参数配置
- 训练历史记录
- 最佳测试准确率

## 开发辅助

本项目使用AI编程辅助完成，遵循以下要求：
- 使用PyTorch作为深度学习框架
- 使用公开的AG News数据集
- 完整实现数据预处理、训练、测试流程
- 输出准确率等评估指标

## 注意事项

- 首次运行会自动下载AG News数据集
- 建议使用GPU加速训练（CUDA）
- 训练时间约5-15分钟（取决于硬件）
