# Create your views here.
from tornado import web
import models


def fix_branch_name(branch_name, project_id):
        if branch_name.find(project_id + "/") != 0:
            branch_name = project_id + "/" + branch_name
        return branch_name


class Commit(web.RequestHandler):

    def post(self):
        project_id = self.get_argument("project")
        branch_name = self.get_argument("branch")
        branch_name = fix_branch_name(branch_name, project_id)
        commit = self.get_argument("commit")
        owner = self.get_argument("owner")
        models.sync_branch(branch_name, commit, owner)
        self.write("{}")


class Merge(web.RequestHandler):

    def post(self):
        target_name = self.get_argument("targetname")
        source_name = self.get_argument("sourcename")
        project_id = self.get_argument("project")
        target_name = fix_branch_name(target_name, project_id)
        source_name = fix_branch_name(source_name, project_id)
        models.branch_merge(target_name, source_name)
        self.write("{}")


class ProjectView(web.RequestHandler):
    def mod_body(self, pk):
        project_id = pk
        branches = []
        for branchname in ["master", "beta", "pre", "dev"]:
            fix_branchname = fix_branch_name(branchname, project_id)
            features = models.branch_feature(fix_branchname)
            upfeature = filter(lambda i: i.STATE.rfind("=") == 0 or i.STATE.rfind("^") == 0, features)
            downfeature = filter(lambda i: i.STATE.rfind("!") == 0 or i.STATE=="", features)
            data = dict(feature=(upfeature, downfeature),
                name=branchname)
            branches.append(data)
        features = models.features(project_id)
        return self.render_string(
            "templates/branch.html",
            branches=branches,
            features=features)

    def get(self, pk):
        body = self.mod_body(pk)
        self.render("templates/base.html", body=body)

class HomeView(ProjectView):

    def get(self):
        return ProjectView.get(self, "1")


class Edit(web.RequestHandler):

    def get(self, pk):
        branch = models.branch_by_id(pk)[0]
        self.render("templates/edit.html", object=branch)

    def post(self, pk):
        img = self.get_argument("img")
        descs = self.get_argument("descs")
        models.update_branch(pk, img, descs)
        self.redirect("/")
