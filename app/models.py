from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Role(db.Model):
    """Role model for user permissions"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # admin, manager, viewer
    description = db.Column(db.String(200))
    permissions = db.Column(db.String(500))  # قائمة الصلاحيات مفصولة بفاصلة
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    users = db.relationship('User', backref='role', lazy=True)
    
    def __repr__(self):
        return f'<Role {self.name}>'

class User(UserMixin, db.Model):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # من أنشأ هذا المستخدم
    
    created_users = db.relationship('User', remote_side=[id], backref='created_by_user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission):
        """التحقق من وجود صلاحية معينة"""
        if self.is_admin:
            return True
        if self.role and permission in (self.role.permissions or '').split(','):
            return True
        return False
    
    def __repr__(self):
        return f'<User {self.username}>'

class Worker(db.Model):
    """Worker model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    hourly_rate_usd = db.Column(db.Float, default=0)  # سعر الساعة بالدولار
    hourly_rate_lbp = db.Column(db.Float, default=0)  # سعر الساعة بالليرة اللبنانية
    advance = db.Column(db.Float, default=0)  # السلفة
    total_hours = db.Column(db.Float, default=0)  # إجمالي ساعات العمل
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    shifts = db.relationship('WorkShift', backref='worker', lazy=True, cascade='all, delete-orphan')
    
    def get_total_earnings_usd(self):
        return self.total_hours * self.hourly_rate_usd
    
    def get_total_earnings_lbp(self):
        return self.total_hours * self.hourly_rate_lbp
    
    def get_total_advances_usd(self):
        """حساب إجمالي السلفات من المحاسبة بالدولار"""
        advances = Accounting.query.filter_by(
            worker_id=self.id, 
            transaction_type='مصروف', 
            category='سلفة'
        ).all()
        return sum(advance.amount_usd for advance in advances)
    
    def get_total_advances_lbp(self):
        """حساب إجمالي السلفات من المحاسبة بالليرة"""
        advances = Accounting.query.filter_by(
            worker_id=self.id, 
            transaction_type='مصروف', 
            category='سلفة'
        ).all()
        return sum(advance.amount_lbp for advance in advances)
    
    def get_balance_usd(self):
        earnings = self.get_total_earnings_usd()
        advances = self.get_total_advances_usd()
        return earnings - advances
    
    def get_balance_lbp(self):
        earnings = self.get_total_earnings_lbp()
        advances = self.get_total_advances_lbp()
        return earnings - advances
    
    def __repr__(self):
        return f'<Worker {self.name}>'

class WorkShift(db.Model):
    """Work shift model"""
    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.Integer, db.ForeignKey('worker.id'), nullable=False)
    shift_type = db.Column(db.String(20), nullable=False)  # صباحي، بعد ظهر
    location = db.Column(db.String(50), nullable=False)  # جبل، سهل
    product_type_id = db.Column(db.Integer, db.ForeignKey('product_type.id'))
    work_type = db.Column(db.String(50))  # تنظيف، تقليم، تشحيل
    hours = db.Column(db.Float, default=0)
    date = db.Column(db.Date, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    product_type = db.relationship('ProductType', backref='shifts')
    
    def __repr__(self):
        return f'<WorkShift {self.worker.name} - {self.shift_type}>'

class ProductType(db.Model):
    """Product type model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    category = db.Column(db.String(50))  # دراق، تفاح، خضروات
    
    productions = db.relationship('Production', backref='product_type', lazy=True, cascade='all, delete-orphan')
    sales = db.relationship('Sales', backref='product_type', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ProductType {self.name}>'

class Production(db.Model):
    """Production record model"""
    id = db.Column(db.Integer, primary_key=True)
    product_type_id = db.Column(db.Integer, db.ForeignKey('product_type.id'), nullable=False)
    location = db.Column(db.String(50))  # جبل، سهل
    quantity = db.Column(db.Float, default=0)  # كمية
    unit = db.Column(db.String(20), default='كجم')  # وحدة قياس
    date = db.Column(db.Date, default=datetime.utcnow)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Production {self.product_type.name} - {self.quantity}>'

class Sales(db.Model):
    """Sales record model"""
    id = db.Column(db.Integer, primary_key=True)
    product_type_id = db.Column(db.Integer, db.ForeignKey('product_type.id'), nullable=False)
    quantity = db.Column(db.Float, default=0)
    unit = db.Column(db.String(20), default='كجم')
    price_per_unit_usd = db.Column(db.Float, default=0)
    price_per_unit_lbp = db.Column(db.Float, default=0)
    total_usd = db.Column(db.Float, default=0)
    total_lbp = db.Column(db.Float, default=0)
    date = db.Column(db.Date, default=datetime.utcnow)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Sales {self.product_type.name}>'

class FuelLog(db.Model):
    """Fuel consumption log"""
    id = db.Column(db.Integer, primary_key=True)
    fuel_type = db.Column(db.String(50), nullable=False)  # مازوت، بنزين
    liters = db.Column(db.Float, nullable=False)
    price_per_liter_usd = db.Column(db.Float, default=0)
    price_per_liter_lbp = db.Column(db.Float, default=0)
    total_usd = db.Column(db.Float, default=0)
    total_lbp = db.Column(db.Float, default=0)
    date = db.Column(db.Date, default=datetime.utcnow)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_remaining_quantity(self):
        """حساب الكمية المتبقية (الكمية الأصلية - المستهلكة)"""
        total_consumed = sum(c.quantity_consumed for c in self.consumptions if c.consumption_type == 'وقود')
        return self.liters - total_consumed
    
    def __repr__(self):
        return f'<FuelLog {self.fuel_type}>'

class Medicine(db.Model):
    """Medicine and pesticide model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, default=0)
    unit = db.Column(db.String(20), default='لتر')
    price_usd = db.Column(db.Float, default=0)
    price_lbp = db.Column(db.Float, default=0)
    date = db.Column(db.Date, default=datetime.utcnow)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_total_value_usd(self):
        """حساب القيمة الإجمالية بالدولار"""
        return self.quantity * self.price_usd
    
    def get_total_value_lbp(self):
        """حساب القيمة الإجمالية بالليرة"""
        return self.quantity * self.price_lbp
    
    def get_remaining_quantity(self):
        """حساب الكمية المتبقية (الكمية الأصلية - المستهلكة)"""
        total_consumed = sum(c.quantity_consumed for c in self.consumptions if c.consumption_type == 'دواء')
        return self.quantity - total_consumed
    
    def __repr__(self):
        return f'<Medicine {self.name}>'

class Fertilizer(db.Model):
    """Fertilizer model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, default=0)
    unit = db.Column(db.String(20), default='كجم')
    price_usd = db.Column(db.Float, default=0)
    price_lbp = db.Column(db.Float, default=0)
    date = db.Column(db.Date, default=datetime.utcnow)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_total_value_usd(self):
        """حساب القيمة الإجمالية بالدولار"""
        return self.quantity * self.price_usd
    
    def get_total_value_lbp(self):
        """حساب القيمة الإجمالية بالليرة"""
        return self.quantity * self.price_lbp
    
    def get_remaining_quantity(self):
        """حساب الكمية المتبقية (الكمية الأصلية - المستهلكة)"""
        total_consumed = sum(c.quantity_consumed for c in self.consumptions if c.consumption_type == 'سماد')
        return self.quantity - total_consumed
    
    def __repr__(self):
        return f'<Fertilizer {self.name}>'

class Consumption(db.Model):
    """Consumption tracking model - for Fuel, Medicine, and Fertilizer"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Link to fuel, medicine, or fertilizer
    fuel_id = db.Column(db.Integer, db.ForeignKey('fuel_log.id'))
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'))
    fertilizer_id = db.Column(db.Integer, db.ForeignKey('fertilizer.id'))
    
    # Consumption details
    consumption_type = db.Column(db.String(50), nullable=False)  # وقود، دواء، سماد
    quantity_consumed = db.Column(db.Float, default=0)
    unit = db.Column(db.String(20), default='')
    date = db.Column(db.Date, default=datetime.utcnow)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    fuel = db.relationship('FuelLog', backref='consumptions')
    medicine = db.relationship('Medicine', backref='consumptions')
    fertilizer = db.relationship('Fertilizer', backref='consumptions')
    
    def __repr__(self):
        return f'<Consumption {self.consumption_type}>'

class Report(db.Model):
    """Report model for storing generated reports"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    report_type = db.Column(db.String(50), nullable=False)  # عمال، إنتاج، مبيعات
    content = db.Column(db.Text)
    generated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='reports')
    
    def __repr__(self):
        return f'<Report {self.title}>'

class Attendance(db.Model):
    """Daily attendance tracking for workers"""
    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.Integer, db.ForeignKey('worker.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='حاضر')  # حاضر، غائب، نصف يوم
    check_in_time = db.Column(db.Time)  # وقت الحضور
    check_out_time = db.Column(db.Time)  # وقت المغادرة
    hours_worked = db.Column(db.Float, default=0)  # عدد ساعات العمل
    notes = db.Column(db.Text)  # ملاحظات
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    worker = db.relationship('Worker', backref='attendance_records')
    
    def __repr__(self):
        return f'<Attendance {self.worker.name} - {self.date}>'

class Accounting(db.Model):
    """Accounting and financial tracking linked to all departments"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Link to different departments
    worker_id = db.Column(db.Integer, db.ForeignKey('worker.id'))  # قسم العمال
    production_id = db.Column(db.Integer, db.ForeignKey('production.id'))  # قسم الإنتاج
    sales_id = db.Column(db.Integer, db.ForeignKey('sales.id'))  # قسم المبيعات
    fuel_id = db.Column(db.Integer, db.ForeignKey('fuel_log.id'))  # قسم الوقود
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'))  # قسم الأدوية والمبيدات
    fertilizer_id = db.Column(db.Integer, db.ForeignKey('fertilizer.id'))  # قسم الأسمدة
    consumption_id = db.Column(db.Integer, db.ForeignKey('consumption.id'))  # قسم الاستهلاك
    
    # Financial tracking
    transaction_type = db.Column(db.String(50), nullable=False)  # إيراد، مصروف
    category = db.Column(db.String(100), nullable=False)  # الفئة: راتب، وقود، أدوية، إلخ
    amount_usd = db.Column(db.Float, default=0)  # المبلغ بالدولار
    amount_lbp = db.Column(db.Float, default=0)  # المبلغ بالليرة اللبنانية
    description = db.Column(db.Text)  # الوصف
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # من أضاف المعاملة
    
    # Relationships
    worker = db.relationship('Worker', backref='accounting_records')
    production = db.relationship('Production', backref='accounting_records')
    sales = db.relationship('Sales', backref='accounting_records')
    fuel = db.relationship('FuelLog', backref='accounting_records')
    medicine = db.relationship('Medicine', backref='accounting_records')
    fertilizer = db.relationship('Fertilizer', backref='accounting_records')
    consumption = db.relationship('Consumption', backref='accounting_records')
    user = db.relationship('User', backref='accounting_transactions')
    
    def __repr__(self):
        return f'<Accounting {self.transaction_type} - {self.amount_usd}>'
