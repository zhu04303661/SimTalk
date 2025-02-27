# Modelica代码生成器

这是一个基于Azure OpenAI GPT-4的Modelica代码生成器，可以通过自然语言描述生成Modelica仿真代码并执行仿真。

<img width="1415" alt="page" src="https://github.com/user-attachments/assets/e227e1dd-02ee-47ab-84b7-0fdac57602b1" />

## 系统架构
![截屏2025-02-24 13 49 39](https://github.com/user-attachments/assets/61eabd34-357d-4e63-b24b-c1f37b56930d)


## 功能特点

- 通过自然语言描述生成Modelica代码
- 自动执行Modelica仿真
- 美观的Web界面
- 实时代码预览
- 仿真结果可视化

## 系统要求

- Python 3.8+
- OpenModelica
- Azure OpenAI API访问权限

## 安装步骤

1. 克隆仓库：
```bash
git clone <repository-url>
cd SimTalk
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
复制`.env.example`文件为`.env`，并填入您的Azure OpenAI API凭证：
```
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=your_endpoint_here
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name_here
```

## 运行应用

1. 启动应用：
```bash
python src/backend/app.py
```

2. 在浏览器中访问：
```
http://localhost:5000
```

## 使用方法

1. 在文本框中输入您想要实现的仿真模型的自然语言描述
2. 点击"生成代码"按钮
3. 查看生成的Modelica代码
4. 查看仿真结果

## 手动仿真方法

1. 在文本框中输入您想要实现的仿真模型的自然语言描述
2. 点击"生成代码"按钮
3. 查看生成的Modelica代码
4. 将生成的Modelica代码复制到test目录下的FallingMarble.mo文件中
5. 在test目录下执行`omc FallingMarble_sim.mos`命令
6. 查看仿真结果

## 注意事项

- 确保已正确安装OpenModelica并将其添加到系统环境变量中
- 确保您有有效的Azure OpenAI API访问权限
- 生成的代码质量取决于输入描述的质量和具体性

## 许可证

MIT 
