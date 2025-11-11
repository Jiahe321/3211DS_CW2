# 3211DS_CW2
## 语言与扩展需求
- Python 3.8+
- VS Code
- Azure Functions扩展，[配置过程](https://learn.microsoft.com/zh-cn/azure/azure-functions/how-to-create-function-vs-code?pivots=programming-language-python) 
- 推荐：GitLens之类的git扩展
- SQL Server ODBC 驱动

## git操作提示
本地写代码, 提交之前请先：
1. git stash暂存本地更改
2. git pull拉取远程最新代码
3. git stash pop 然后commit和push
- 注意，不要把本地配置文件夹交上来，如.vscode，__pycache__。可以直接删掉这些文件夹再提交。
- 确定本地能跑通之后再push上来。

实在不会请咨询GPT老师
## Azure操作指南
* [免费部署 Azure SQL 数据库](https://learn.microsoft.com/zh-cn/azure/azure-sql/database/free-offer?view=azuresql)
* [使用 Visual Studio Code 创建函数代码并将其部署到 Azure](https://learn.microsoft.com/zh-cn/azure/azure-functions/how-to-create-function-vs-code?pivots=programming-language-python)
* [在 Azure 门户中创建函数应用](https://learn.microsoft.com/zh-cn/azure/azure-functions/functions-create-function-app-portal?pivots=flex-consumption-plan&tabs=core-tools)


## 任务列表
- Task 1: Simulated Data （差不多完成了）
- Task 2: Statistics
- Task 3: Realistic Scenario

需要先创建一个空文件夹并连接到Azure Function，然后把代码放进去。
推荐做法:自己写的代码放在一个utils文件夹里，然后在Azure Function的文件里import进来。全部完成之后再考虑部署到Azure上。
