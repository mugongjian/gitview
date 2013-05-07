#coding=utf-8
from torndb import Connection
from config import db_config
conn = Connection(db_config["host"], db_config["db"], user=db_config["user"], password=db_config["password"])
IS_FEATURE_BRANCH = "0"
IS_MERGE_BRANCH = "1"

class Data(object):
    pass


def is_parent_branch(branch_name, parent_name):
    return branch_name.find(parent_name) == 0

def branch_add_commit(branch_name, commit, state=""):
    """ branch merge commit """
    select_sql = ("SELECT BRANCH_NAME, HEAD FROM BRANCH_MERGE" +
    " WHERE BRANCH_NAME=%s and HEAD=%s")
    if not conn.query(select_sql, *(branch_name, commit)):
        conn.execute("INSERT INTO BRANCH_MERGE (BRANCH_NAME, HEAD, STATE) VALUES(%s, %s, %s)",
            *(branch_name, commit, state))


def commit_is_flat(commit, branch_name):
    #已经判断过了
    commit_state = conn.query(
        "SELECT STATE FROM BRANCH_MERGE WHERE BRANCH_NAME=%s AND HEAD=%s",
        *(branch_name, commit))[0]
    if commit_state.STATE in ["^", "!^"]:
        return True
    branch_counts = conn.query(
        "SELECT COUNT(ID) AS COUNTS FROM BRANCH WHERE NAME REGEXP %s",
        *(branch_name + "(/.*)?",))[0].COUNTS
    merge_counts = conn.query(
        ("SELECT COUNT(ID) AS COUNTS FROM BRANCH_MERGE WHERE BRANCH_NAME REGEXP %s" +
        " AND HEAD=%s AND STATE!='!'"),
        *(branch_name + "(/.*)?", commit,))[0].COUNTS
    return branch_counts and merge_counts and branch_counts <= merge_counts

def water_commit_is_flat(commit, branch_name):
    commit_state = conn.query(
        "SELECT STATE FROM BRANCH_MERGE WHERE BRANCH_NAME=%s AND HEAD=%s",
        *(branch_name, commit))[0]
    if commit_state.STATE == "!^":
        return True
    branch_counts = conn.query(
        "SELECT COUNT(ID) AS COUNTS FROM BRANCH WHERE NAME REGEXP %s",
        *(branch_name + "(/.*)?",))[0].COUNTS
    merge_counts = conn.query(
        ("SELECT COUNT(ID) AS COUNTS FROM BRANCH_MERGE WHERE BRANCH_NAME REGEXP %s"+
        " AND HEAD=%s AND STATE='!'"),
        *(branch_name + "(/.*)?", commit,))[0].COUNTS
    return branch_counts and merge_counts and branch_counts <= merge_counts
## 分支操作
def create_branch(branch_name, head, owner, state=IS_FEATURE_BRANCH, img="", branch_desc=""):
    sql = ("INSERT INTO BRANCH (NAME,HEAD,OWNER,STATE,IMG,DESCS) " +
        "VALUES (%s, %s, %s, %s, %s,%s)")
    conn.execute(sql,*(branch_name, head, owner, state, img, branch_desc))


def update_branch_commit(branch_name, head, owner):
    sql = "UPDATE BRANCH SET HEAD=%s ,OWNER=%s WHERE NAME=%s"
    conn.execute(sql, *(head, owner, branch_name))


def sync_branch(branch_name, head, owner):
    branch = conn.query("SELECT NAME, STATE FROM BRANCH WHERE NAME=%s", *(branch_name,))
    if branch:
        if branch[0].STATE == IS_FEATURE_BRANCH:
            update_branch_commit(branch_name, head, owner)
        elif branch[0].STATE == IS_MERGE_BRANCH:
            create_branch(branch_name + "/" + head, head, owner)
            branch_add_commit(branch_name, head)
    else:
        create_branch(branch_name, head, owner)
#合并操作
def _stage_merge_feature(target_name, head):
    """ [merging ]< [feature]"""
    branch_add_commit(target_name, head)


def _feature_sync_stage(feature_name, stage_branch_name):
    """feature merge other feature which merged into <stage>"""
    if not is_parent_branch(feature_name, stage_branch_name):
        """feature branch only merge where they came from"""
        return
    commits = conn.query(
        "SELECT BRANCH_NAME, HEAD, STATE FROM BRANCH_MERGE WHERE BRANCH_NAME=%s",
        *(stage_branch_name,))
    #feature_head 是提交到上级分支的,没必要再合并到功能分支
    flat_commits = []
    water_commits = []
    for commit in commits:
        branch_add_commit(feature_name, commit.HEAD, "!" if commit.STATE == "!" else "")
        if commit_is_flat(commit.HEAD, stage_branch_name):
            flat_commits.append(commit)
        if commit.STATE == "!" and water_commit_is_flat(commit.HEAD, stage_branch_name):
            water_commits.append(commit)
    if flat_commits:
        for commit in flat_commits:
            conn.execute(
                "DELETE FROM BRANCH_MERGE WHERE BRANCH_NAME REGEXP %s AND HEAD=%s",
                *("^" + stage_branch_name + "/.*", commit.HEAD))
        conn.execute(
            "UPDATE BRANCH_MERGE SET STATE='^' WHERE BRANCH_NAME=%s",
            *(stage_branch_name,))
    if water_commits:
        for commit in water_commits:
            conn.execute(
                "DELETE FROM BRANCH_MERGE WHERE BRANCH_NAME REGEXP %s AND HEAD=%s AND STATE='!'",
                *("^" + stage_branch_name + "/.*", commit.HEAD))
        conn.execute(
            "UPDATE BRANCH_MERGE SET STATE='!^' WHERE BRANCH_NAME=%s",
            *(stage_branch_name,))


def _up_merge_down(up_name, down_name):
    """master<beta, beta<pre, pre<dev"""
    commits = conn.query(
        "SELECT HEAD FROM BRANCH_MERGE WHERE BRANCH_NAME=%s AND STATE !='!'",
        *(down_name,))
    flat_commits = []
    for commit in commits:
        branch_add_commit(up_name, commit.HEAD)
        if commit_is_flat(commit.HEAD, down_name):
            flat_commits.append(commit)
    if flat_commits:
        for commit in flat_commits:
            conn.execute(
                "DELETE FROM BRANCH_MERGE WHERE BRANCH_NAME REGEXP %s and HEAD=%s",
                *("^" + down_name, commit.HEAD))
            conn.execute(
                "UPDATE BRANCH_MERGE SET STATE='=' WHERE BRANCH_NAME=%s AND HEAD=%s",
                *(up_name, commit.HEAD))


def _down_merge_up(down_name, up_name):
    """master>beta, beta>pre, pre>dev"""
    #state contains "^":down is flat
    commits = conn.query(
        "SELECT HEAD FROM BRANCH_MERGE WHERE BRANCH_NAME=%s AND STATE!='^' AND STATE !='!^'",
        *(up_name,))
    water_flat_commits = []
    for commit in commits:
        branch_add_commit(down_name, commit.HEAD, "!")
        import logging
        logging.error(commit)
        if water_commit_is_flat(commit.HEAD, down_name):
            water_flat_commits.append(commit)

    if water_flat_commits:
        for commit in water_flat_commits:
            conn.execute(
                ("DELETE FROM BRANCH_MERGE WHERE BRANCH_NAME REGEXP %s AND HEAD=%s"+
                " AND (STATE='!' OR STATE='!^')"),
                *("^" + down_name, commit.HEAD))
            conn.execute(
                "UPDATE BRANCH_MERGE SET STATE='!^' WHERE BRANCH_NAME=%s",
                *(up_name,))


def branch_merge(target_name, source_name):
    """source branch must exists """
    if target_name == source_name:
        return
    branch_detail_sql = "SELECT NAME, HEAD, STATE FROM BRANCH WHERE NAME=%s"
    target_branch = conn.query(branch_detail_sql, *(target_name,))
    if target_branch:
        target_branch = target_branch[0]
    else:
        create_branch(target_name, "", "", state=IS_MERGE_BRANCH)
        target_branch = Data()
        target_branch.STATE = IS_MERGE_BRANCH
    source_branch = conn.query(branch_detail_sql, *(source_name,))
    if source_branch:
        source_branch = source_branch[0]
    else:
        create_branch(source_name, "", "", state=IS_MERGE_BRANCH)
        source_branch = Data()
        source_branch.STATE = IS_MERGE_BRANCH
    if target_branch.STATE == IS_FEATURE_BRANCH:
        if source_branch.STATE == IS_MERGE_BRANCH:
            _feature_sync_stage(target_name, source_name)
    elif target_branch.STATE == IS_MERGE_BRANCH:
        if source_branch.STATE == IS_FEATURE_BRANCH:
            _stage_merge_feature(target_name, source_branch.HEAD)
        elif source_branch.STATE == IS_MERGE_BRANCH:
            source_index = target_name.find(source_name)
            target_index = source_name.find(target_name)
            if source_index >-1 or target_index >-1:
                if source_index == 0:
                    _down_merge_up(target_name, source_name)
                elif target_index == 0:
                    _up_merge_down(target_name, source_name)
            else:
                branch_order = ["dev", "pre", "beta", "master"]
                relative_target_name = target_name[target_name.find("/") + 1:]
                target_index = branch_order.index(relative_target_name)
                relative_source_name = source_name[source_name.find("/") + 1:]
                source_index = branch_order.index(relative_source_name)
                if target_index > source_index:
                    _up_merge_down(target_name, source_name)
                elif target_index < source_index:
                    _down_merge_up(target_name, source_name)


def branch_feature(branch_name):
    sql = ("SELECT B.NAME,B.DESCS,B.IMG, B.HEAD, B.ID,BM.STATE FROM BRANCH B, BRANCH_MERGE BM" +
    " WHERE BM.BRANCH_NAME=%s and B.HEAD=BM.HEAD")
    feature = conn.query(sql, *(branch_name,))
    return feature


def features():
    features = conn.query("SELECT ID, NAME, DESCS, STATE, IMG, HEAD FROM BRANCH WHERE STATE='0'")
    for feature in features:
        merges = branch_feature(feature.NAME)
        merges = filter(lambda i: i.HEAD != feature.HEAD, merges)
        feature.merges = merges
    return features


def branch_by_id(pk):
    return conn.query(
        "SELECT NAME,IMG, DESCS,HEAD FROM BRANCH WHERE ID=%s",
        *(pk, ))


def update_branch(pk ,img, descs):
    conn.execute(
        "UPDATE BRANCH SET IMG=%s ,DESCS=%s WHERE ID=%s",
        *(img, descs, pk))


def init_project(project_id):
    data = []
    for branch in ["master", "beta", "pre", "dev"]:
        data.append((project_id+"/"+ branch, "1"))
    conn.executemany(
        "INSERT INTO BRANCH (NAME, STATE) VALUES (%s, %s)",
        data)