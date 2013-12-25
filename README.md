gitview
=======

show progress of features,not focus on code ,focus on feature

配置如下:
1 保证gitw 脚本可执行
  需要python2.7
  保证gitw 在可执行路径
  chmod u+x gitw
2 添加如下内容到~/.bash_profile

export REAL_GIT_PATH=`which git`
export MERGE_HOST='localhost:8003'
export GIT_USER='your name'

3 source ~/.bash_profile

4 进入一个git仓库,echo <项目编号> 1>PROJECTID

5 使用 gitw commit 提交代码

