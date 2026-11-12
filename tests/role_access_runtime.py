"""Isolated authorization tests against the CRM runtime installed in the Docker image.

No network, production credentials, or database writes. The tested functions
are loaded from /srv/backend/app/main.py, not copied into the test suite.
"""
import ast
from pathlib import Path
from types import SimpleNamespace

MAIN = Path('/srv/backend/app/main.py')
assert MAIN.exists(), f'Missing runtime at {MAIN}'
source = MAIN.read_text()
tree = ast.parse(source)

class HTTPException(Exception):
    def __init__(self, status_code, detail):
        self.status_code, self.detail = status_code, detail
        super().__init__(str(detail))

class Column:
    def __init__(self, key):
        self.key = key
    def __eq__(self, other):
        return lambda record: getattr(record, self.key) == other

class Lead:
    company_id = Column('company_id')
    assigned_user_id = Column('assigned_user_id')

class User:
    company_id = Column('company_id')
    email = Column('email')
    name = Column('name')

class Query:
    def __init__(self, rows):
        self.rows = rows
    def filter(self, test):
        return Query([row for row in self.rows if test(row)])
    def order_by(self, *_):
        return self
    def all(self):
        return self.rows
    def first(self):
        return self.rows[0] if self.rows else None

class DB:
    def __init__(self, leads, users):
        self.leads, self.users = leads, users
        self.commits = 0
    def query(self, model):
        return Query(self.leads if model is Lead else self.users)
    def get(self, model, ident):
        return next((x for x in (self.leads if model is Lead else self.users) if x.id == ident), None)
    def commit(self):
        self.commits += 1
    def refresh(self, record):
        pass

def same_company(u, company_id):
    if u.company_id != company_id:
        raise HTTPException(403, 'Cross-company access denied')

def audit(*args, **kwargs):
    pass

def lead_view(lead):
    return {'id': lead.id, 'assigned_user_id': lead.assigned_user_id}

def extract_function(name, namespace):
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    assert len(functions) == 1, (name, len(functions))
    node = functions[0]
    node.decorator_list = []
    node.returns = None
    node.type_comment = None
    for a in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]:
        a.annotation = None
    node.args.defaults = []
    node.args.kw_defaults = [None for _ in node.args.kwonlyargs]
    compiled = compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(MAIN), 'exec')
    exec(compiled, namespace)
    return namespace[name]

namespace = dict(Lead=Lead, User=User, HTTPException=HTTPException,
                 same_company=same_company, audit=audit, lead_view=lead_view)
visible = extract_function('visible_leads_query', namespace)
tenant = extract_function('tenant_lead', namespace)
assign = extract_function('secure_assign_lead', namespace)
create_user = extract_function('secure_create_user', namespace)
get_users = extract_function('secure_users', namespace)

owner = SimpleNamespace(id='owner', company_id='roof', role='OWNER')
rep_a = SimpleNamespace(id='rep-a', company_id='roof', role='REP')
rep_b = SimpleNamespace(id='rep-b', company_id='roof', role='REP')
other = SimpleNamespace(id='outsider', company_id='outside', role='OWNER')
users = [
    SimpleNamespace(id='owner', company_id='roof', role='OWNER', active=True, name='Owner', email='owner@example.test'),
    SimpleNamespace(id='rep-a', company_id='roof', role='REP', active=True, name='Rep A', email='a@example.test'),
    SimpleNamespace(id='rep-b', company_id='roof', role='REP', active=True, name='Rep B', email='b@example.test'),
    SimpleNamespace(id='inactive', company_id='roof', role='REP', active=False, name='Inactive', email='off@example.test'),
    SimpleNamespace(id='outsider', company_id='outside', role='OWNER', active=True, name='External', email='out@example.test'),
]
leads = [
    SimpleNamespace(id='one', company_id='roof', assigned_user_id='rep-a'),
    SimpleNamespace(id='two', company_id='roof', assigned_user_id='rep-b'),
    SimpleNamespace(id='three', company_id='outside', assigned_user_id='outsider'),
]
db = DB(leads, users)

assert {x.id for x in visible(db, owner).all()} == {'one', 'two'}
assert {x.id for x in visible(db, rep_a).all()} == {'one'}
assert {x.id for x in visible(db, rep_b).all()} == {'two'}
assert {x.id for x in visible(db, other).all()} == {'three'}
assert tenant(db, owner, 'two').id == 'two'
assert tenant(db, rep_a, 'one').id == 'one'

def rejects(expected_code, fn):
    try:
        fn()
    except HTTPException as ex:
        assert ex.status_code == expected_code, (ex.status_code, expected_code)
    else:
        raise AssertionError('Expected HTTP ' + str(expected_code))

rejects(404, lambda: tenant(db, rep_a, 'two'))
rejects(403, lambda: tenant(db, owner, 'three'))
rejects(404, lambda: tenant(db, rep_a, 'missing'))
rejects(400, lambda: assign('one', SimpleNamespace(assigned_user_id='outsider'), owner, db))
rejects(400, lambda: assign('one', SimpleNamespace(assigned_user_id='inactive'), owner, db))
assert assign('one', SimpleNamespace(assigned_user_id='rep-b'), owner, db)['assigned_user_id'] == 'rep-b'
assert {x.id for x in visible(db, rep_a).all()} == set()
assert {x.id for x in visible(db, rep_b).all()} == {'one', 'two'}
assert len(get_users(owner, db)) == 5
rejects(400, lambda: create_user(SimpleNamespace(name='No', email='owner2@example.test', role='OWNER'), owner, db))

# The FastAPI Depends(require_roles('OWNER')) wrapper is part of the security
# boundary. Confirm it remains wired to the actual route parameter rather
# than treating direct function calls as representative authorization checks.
for func_name in ('secure_users', 'secure_create_user', 'secure_assign_lead'):
    route = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == func_name)
    assert any("require_roles('OWNER')" in ast.unparse(d) for d in route.args.defaults), func_name

print('PASS: owner company-wide visibility; reps assigned-only; other tenant isolated')
print('PASS: direct lead read denied; unknown lead denied; invalid assignees rejected')
print('PASS: reassignment updates rep visibility; duplicate OWNER creation rejected')
print('PASS: all three owner-only routes retain FastAPI role dependencies')
print('NOTE: isolated runtime tests are not two real authenticated logins')
