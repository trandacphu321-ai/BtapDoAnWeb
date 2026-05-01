from shop import db


class Admin(db.Document):
    name = db.StringField(max_length=50, required=True)
    username = db.StringField(max_length=80, unique=True, required=True)
    email = db.StringField(max_length=120, unique=True, required=True)
    password = db.StringField(max_length=180, required=True)
    profile = db.StringField(max_length=180, required=True, default='profile.jpg')
    # RBAC - Phân quyền: 'superadmin', 'manager', 'staff_warehouse', 'staff_support'
    role = db.StringField(max_length=30, default='superadmin')

    meta = {'collection': 'admin', 'strict': False}

    # ---- Helper properties ----
    @property
    def is_superadmin(self):
        return self.role == 'superadmin'

    @property
    def can_manage_products(self):
        return self.role in ('superadmin', 'manager', 'staff_warehouse')

    @property
    def can_view_orders(self):
        return self.role in ('superadmin', 'manager', 'staff_support', 'staff_warehouse')

    @property
    def can_manage_orders(self):
        return self.role in ('superadmin', 'manager', 'staff_support')

    @property
    def can_view_revenue(self):
        return self.role in ('superadmin', 'manager')

    @property
    def can_manage_admins(self):
        return self.role == 'superadmin'

    def __repr__(self):
        return '<User %r>' % self.username
