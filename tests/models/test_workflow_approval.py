from aap_chatops.models.workflow_approval import WorkflowApproval


def test_workflow_name_returns_name_when_present(make_approval_payload):
    approval = WorkflowApproval.model_validate(make_approval_payload())
    assert approval.workflow_name == "(TEST) flow/james_playground"


def test_workflow_name_returns_none_when_absent(make_approval_payload):
    payload = make_approval_payload()
    del payload["summary_fields"]["workflow_job"]
    approval = WorkflowApproval.model_validate(payload)
    assert approval.workflow_name is None


def test_created_by_username_returns_username_when_present(make_approval_payload):
    approval = WorkflowApproval.model_validate(make_approval_payload())
    assert approval.created_by_username == "YoungJamesY"


def test_created_by_username_returns_none_when_absent(make_approval_payload):
    payload = make_approval_payload()
    del payload["summary_fields"]["created_by"]
    approval = WorkflowApproval.model_validate(payload)
    assert approval.created_by_username is None
