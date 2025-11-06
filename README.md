# 3211DS_CW2
## 语言与扩展需求
- Python 3.8+
- VS Code
- Azure Functions扩展，用于本地连接Azure Function，详细配置过程链接: https://learn.microsoft.com/zh-cn/azure/azure-functions/how-to-create-function-vs-code?pivots=programming-language-python
- git可以使用一些好用的插件，比如GitLens之类的，这样可以不用手动敲代码
- 安装 SQL Server ODBC 驱动

## git操作提示
本地写代码, 提交之前请先：
1. git stash暂存本地更改
2. git pull拉取远程最新代码
3. 照理来说不会有冲突，冲突了自己解决一下，确定能编译能跑再执行下一步
4. git stash pop 然后commit和push (我这里是git push origin master:main)
- 注意，不要把本地配置文件夹交上来，比如.vscode，__pycache__之类的。可以直接删掉这些文件夹再提交。

实在不会请咨询GPT老师

## 任务列表
- Task 1: Simulated Data
- Task 2: Statistics
- Task 3: Realistic Scenario

需要先创建一个空文件夹，把它连接到Azure Function，然后把代码放进去。推荐做法是自己写的代码放在一个单独的utils文件夹里，然后在Azure Function的文件里import进来。确定本地能跑通之后再push上来。全部完成之后再考虑部署到Azure上。
