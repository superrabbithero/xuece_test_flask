from app.models import db, Issue, StatusChangeRecord

class IssueRepository:
    @staticmethod
    def create_issue(content, images=None, submitter_id=None, submitter_name=None):
        issue = Issue(
            content=content,
            images=images or [],
            submitter_id=submitter_id,
            submitter_name=submitter_name
        )
        db.session.add(issue)
        db.session.commit()
        return issue

    @staticmethod
    def update_issue_status(issue_id, new_status, operator_id, operator_name, 
                           gitee_url=None, ignore_reason=None):
        issue = Issue.query.get(issue_id)
        if not issue:
            return None
            
        record = StatusChangeRecord(
            issue_id=issue_id,
            old_status=issue.status,
            new_status=new_status,
            operator_id=operator_id,
            operator_name=operator_name,
            extra_info={
                "gitee_url": gitee_url,
                "ignore_reason": ignore_reason
            }
        )
        
        issue.status = new_status
        issue.handler_id = operator_id
        issue.handler_name = operator_name
        issue.resolved_at = datetime.utcnow()
        
        if new_status in ['claimed', 'resolved']:
            issue.gitee_url = gitee_url
        elif new_status == 'ignored':
            issue.ignore_reason = ignore_reason
        
        db.session.add(record)
        db.session.commit()
        return issue

    @staticmethod
    def get_issues(filters=None):
        query = Issue.query
        
        if filters:
            if 'start_time' in filters and 'end_time' in filters:
                query = query.filter(Issue.created_at.between(filters['start_time'], filters['end_time']))
            if 'status' in filters:
                query = query.filter_by(status=filters['status'])
                
        return query.order_by(Issue.created_at.desc()).all()

    @staticmethod
    def get_issue_by_id(issue_id):
        return Issue.query.get(issue_id)

class DingTalkRepository:
    @staticmethod
    def parse_bug_report(content, user_id, user_name):
        """解析钉钉消息格式"""
        return {
            "content": content.strip("%bug").strip(),
            "submitter_id": user_id,
            "submitter_name": user_name
        }