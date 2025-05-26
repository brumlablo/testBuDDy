# TestBuDDy-Requirements-coverage
# NFR-02, FR-09, FR-10

import json
from jira import JIRA
import abc
from app import dbs
from base_objects import Bug


class IssueTrackerFactory:
    """Factory that handles user input information about their chosen CI
     and creates needed CI object."""

    def create_issue_tracker(self, project):
        if project.issue_tracker == "jira":
            return JiraIssueTracker(project)
        else:
            raise NotImplemented("Requested Issue Tracker NOT found.")


class BaseIssueTrackerAdapter(abc.ABC):  # abstract class
    """Adapter for CI communication """

    @abc.abstractmethod
    def __init__(self, project):
        self.params = project.get_issue_tracker_params()

    @abc.abstractmethod
    def connect(self):
        raise NotImplemented

    @abc.abstractmethod
    def get_bug_status(self, type):
        raise NotImplemented

    @abc.abstractmethod
    def send_data_to_issue_tracker_bug(self, bug_id):
        raise NotImplemented

    @abc.abstractmethod
    def update_bugs_from_issue_tracker(self):
        raise NotImplemented

    @abc.abstractmethod
    def check_if_issue_exists(self, bug):
        raise NotImplemented


class JiraIssueTracker(BaseIssueTrackerAdapter):

    def __init__(self, project):
        super().__init__(project)
        self.project = None
        self.jira = None
        self.parse_issue_tracker_params()
        self.connect()

    def parse_issue_tracker_params(self):
        try:
            self.server = self.params['server']
            self.username = self.params['username']
            self.password = self.params['password']
            self.project_shortcut = self.params['project_shortcut']
        except KeyError:
            raise RuntimeError("Missing Issue Tracker parameter, please modify your project 'issue_tracker_params' "
                               "with 'server' and credentials.")

    def get_bug_status(self, type):
        if type == "open":
            return "open"
        if type == "closed":
            return "closed"

    def connect(self):
        try:
            if not self.project or not self.jira:
                self.jira = JIRA(options={"server": self.server}, basic_auth=(self.username, self.password))
                self.project = self.jira.project(self.project_shortcut)
        except Exception as e:
            raise RuntimeError("Error connecting to JIRA or accessing your project in JIRA.")

    def send_data_to_issue_tracker_bug(self, bugs):
        """Send modified bugs to their JIRA issues."""
        # get bug link
        # send data to bug link
        self.connect()
        bugs_with_link = list(filter(lambda bug: bug.link, bugs))
        general_b_report = "--------------------TestBuDDy bug with internal id: '{BUG_ID}' found!------------------\n"\
                     + "\nfound in these CI_runs: \n{{code:json}}\n{CI_RUNS_DATA}\n{{code}}\n"\
                     + "bug data: \n{{code:json}}\n{BUG_DATA}\n{{code}}\n" \
                     + "----------------------------------------------------------------------------------------\n"
        for b in bugs_with_link:
            if not self.check_if_issue_exists(b):
                continue
            issue = self.jira.issue(b.link)
            if issue.fields.status.name in ["Closed", "Done"]:
                b.status = "closed"
                print("Bug '" + str(b.id) + "' already closed.")
                continue
            b_report = general_b_report.format(BUG_ID=str(b.id),
                                               BUG_DATA=json.dumps((b.to_dict(0))["data"], indent=4),
                                               CI_RUNS_DATA=json.dumps((b.to_dict(0))["ci_runs_affected"], indent=4))
            self.jira.add_comment(issue, b_report)
            print("Bug '" + str(b.id) + "' received new comment in its connected Issue Tracker issue under link: "
                  + b.link)

    def check_if_issue_exists(self, bug):
        self.connect()
        try:
            issue = self.jira.issue(bug.link)
            if not issue:
                raise RuntimeError()
        except Exception as e:
            print("Bug with id: " + str(bug.id) +
                  " - there was NO connected Issue found in your Issue tracker with bug link: " + bug.link)
            return False
        return True

    def update_bugs_from_issue_tracker(self):
        self.connect()
        bugs = dbs.session.query(Bug.dbs_model).filter(Bug.dbs_model.project_id == self.project.id).all()
        bugs_with_link = list(filter(lambda bug: bug.link, bugs))
        for b in bugs_with_link:
            if not self.check_if_issue_exists(b):
                continue
            issue = self.jira.issue(b.link)
            b.status = issue.fields.status.name
            dbs.session.flush()
            print("Bug '" + str(b.id) + "' changed status to '" + b.status + "' according to Issue Tracker.")
