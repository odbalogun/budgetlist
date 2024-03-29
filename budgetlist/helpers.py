from flask import json
from wtforms.validators import ValidationError

# constants
list_account_types = ['Basic User', 'Super User', 'Administrator']
list_project_status = ['Pending', 'Ongoing', 'Completed', 'Suspended']
list_task_status = ['Pending', 'Ongoing', 'Completed', 'Suspended']
list_percentages = [(0, '0%'), (10, '10%'), (20, '20%'), (30, '30%'), (40, '40%'), (50, '50%'), (60, '60%'), (70, '70%'),
                    (80, '80%'), (90, '90%'), (100, '100%')]

list_budget_types = ['Operational Ex.', 'Capital Ex.', 'Consultancy', 'Moveables']
list_priority = ['Normal', 'Medium', 'High']

list_audit_types = ['User Access', 'Activity Creation', 'Task Creation', 'Task Update', 'Budget Creation',
                    'User Management', 'Period Management', 'Department Management', 'Project Management',
                    'Sub Budget Creation', 'Sub Budget Management', 'Budget Management']
list_audit_models = ['User', 'Project', 'Task', 'Budget', 'Sub Budget', 'Period']

def dump_datetime(value):
    """Deserialize datetime object into string form for JSON processing."""
    if value is None:
        return None
    return {'date': value.strftime("%d %b %Y"), 'time': value.strftime("%H:%M:%S")}

def to_json(inst, cls):
    """
    Jsonify the sql alchemy query result.
    """
    convert = dict()
    # add your coversions for things like datetime's
    # and what-not that aren't serializable.
    d = dict()
    for c in cls.__table__.columns:
        v = getattr(inst, c.name)
        if c.type in convert.keys() and v is not None:
            try:
                d[c.name] = convert[c.type](v)
            except:
                d[c.name] = "Error:  Failed to covert using ", str(convert[c.type])
        elif v is None:
            d[c.name] = str()
        else:
            d[c.name] = v
    return json.dumps(d)


class Unique(object):
    def __init__(self, model, field, message=u'This element already exists.'):
        self.model = model
        self.field = field
        self.message = message

    def __call__(self, form, field):
        check = self.model.query.filter(self.field == field.data).first()
        if check:
            raise ValidationError(self.message)


class Numeric(object):
    def __init__(self, model, field, message=u'This element must be numeric'):
        self.model = model
        self.field = field
        self.message = message

    def __call__(self, form, field):
        if field.data and not field.data.isdigit():
            raise ValidationError(self.message)