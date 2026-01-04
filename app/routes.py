from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user, login_user, logout_user
from datetime import datetime, timedelta, date
from functools import wraps
from app import db
from app.models import (User, Role, Worker, WorkShift, ProductType, Production, Sales, 
                        FuelLog, Medicine, Fertilizer, Consumption, Report, Attendance, Accounting)

# ==================== Permission Decorators ====================
def require_permission(permission):
    """Decorator to check if user has specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('يجب تسجيل الدخول أولاً', 'warning')
                return redirect(url_for('auth.login'))
            
            # Admin users have all permissions
            if current_user.is_admin:
                return f(*args, **kwargs)
            
            # Check if user has the required permission
            if current_user.has_permission(permission):
                return f(*args, **kwargs)
            
            flash('ليس لديك صلاحية للقيام بهذا الإجراء', 'danger')
            return redirect(url_for('main.index'))
        
        return decorated_function
    return decorator

def inject_now():
    """Inject current datetime into all templates"""
    return dict(now=datetime.now())

# Create blueprints
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
workers_bp = Blueprint('workers', __name__, url_prefix='/workers')
production_bp = Blueprint('production', __name__, url_prefix='/production')
sales_bp = Blueprint('sales', __name__, url_prefix='/sales')
fuel_bp = Blueprint('fuel', __name__, url_prefix='/fuel')
medicines_bp = Blueprint('medicines', __name__, url_prefix='/medicines')
consumption_bp = Blueprint('consumption', __name__, url_prefix='/consumption')
reports_bp = Blueprint('reports', __name__, url_prefix='/reports')
settings_bp = Blueprint('settings', __name__, url_prefix='/settings')
attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')
accounting_bp = Blueprint('accounting', __name__, url_prefix='/accounting')

# ==================== Main Routes ====================
@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        workers_count = Worker.query.count()
        total_shifts = WorkShift.query.count()
        recent_shifts = WorkShift.query.order_by(WorkShift.date.desc()).limit(5).all()
        
        # Attendance statistics
        today = datetime.now().date()
        today_attendance = Attendance.query.filter_by(date=today).count()
        today_present = Attendance.query.filter(
            Attendance.date == today,
            Attendance.status == 'حاضر'
        ).count()
        
        # Accounting summary
        all_records = Accounting.query.all()
        total_income = sum(r.amount_usd for r in all_records if r.transaction_type == 'إيراد')
        total_expense = sum(r.amount_usd for r in all_records if r.transaction_type == 'مصروف')
        
        return render_template('dashboard.html', 
                             workers_count=workers_count, 
                             total_shifts=total_shifts, 
                             recent_shifts=recent_shifts,
                             today_attendance=today_attendance,
                             today_present=today_present,
                             total_income=total_income,
                             total_expense=total_expense)
    return redirect(url_for('auth.login'))

# ==================== Authentication Routes ====================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=request.form.get('remember'))
            return redirect(url_for('main.index'))
        flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('كلمات المرور غير متطابقة', 'danger')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(username=username).first():
            flash('اسم المستخدم موجود بالفعل', 'danger')
            return redirect(url_for('auth.register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('تم التسجيل بنجاح، يرجى تسجيل الدخول', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('auth.login'))

# ==================== Workers Routes ====================
@workers_bp.route('/')
@login_required
@require_permission('view_workers')
def workers_list():
    workers = Worker.query.all()
    return render_template('workers/list.html', workers=workers)

@workers_bp.route('/add', methods=['GET', 'POST'])
@login_required
@require_permission('add_workers')
def add_worker():
    if request.method == 'POST':
        worker = Worker(
            name=request.form.get('name'),
            phone=request.form.get('phone'),
            hourly_rate_usd=float(request.form.get('hourly_rate_usd', 0)),
            hourly_rate_lbp=float(request.form.get('hourly_rate_lbp', 0)),
            advance=float(request.form.get('advance', 0))
        )
        db.session.add(worker)
        db.session.commit()
        flash('تم إضافة العامل بنجاح', 'success')
        return redirect(url_for('workers.workers_list'))
    
    return render_template('workers/add.html')

@workers_bp.route('/<int:worker_id>')
@login_required
@require_permission('view_workers')
def worker_detail(worker_id):
    worker = Worker.query.get_or_404(worker_id)
    shifts = WorkShift.query.filter_by(worker_id=worker_id).all()
    return render_template('workers/detail.html', worker=worker, shifts=shifts)

@workers_bp.route('/<int:worker_id>/edit', methods=['GET', 'POST'])
@login_required
@require_permission('edit_workers')
def edit_worker(worker_id):
    worker = Worker.query.get_or_404(worker_id)
    if request.method == 'POST':
        worker.name = request.form.get('name')
        worker.phone = request.form.get('phone')
        worker.hourly_rate_usd = float(request.form.get('hourly_rate_usd', 0))
        worker.hourly_rate_lbp = float(request.form.get('hourly_rate_lbp', 0))
        worker.advance = float(request.form.get('advance', 0))
        db.session.commit()
        flash('تم تحديث بيانات العامل بنجاح', 'success')
        return redirect(url_for('workers.worker_detail', worker_id=worker_id))
    
    return render_template('workers/edit.html', worker=worker)

@workers_bp.route('/<int:worker_id>/add_shift', methods=['GET', 'POST'])
@login_required
@require_permission('add_workers')
def add_shift(worker_id):
    worker = Worker.query.get_or_404(worker_id)
    if request.method == 'POST':
        shift = WorkShift(
            worker_id=worker_id,
            shift_type=request.form.get('shift_type'),  # صباحي، بعد ظهر
            location=request.form.get('location'),  # جبل، سهل
            product_type_id=request.form.get('product_type_id') or None,
            work_type=request.form.get('work_type'),  # تنظيف، تقليم، تشحيل
            hours=float(request.form.get('hours', 0)),
            date=datetime.strptime(request.form.get('date'), '%Y-%m-%d'),
            notes=request.form.get('notes')
        )
        worker.total_hours += shift.hours
        db.session.add(shift)
        db.session.commit()
        flash('تم إضافة النوبة بنجاح', 'success')
        return redirect(url_for('workers.worker_detail', worker_id=worker_id))
    
    product_types = ProductType.query.all()
    return render_template('workers/add_shift.html', worker=worker, product_types=product_types)

# ==================== Production Routes ====================
@production_bp.route('/')
@login_required
@require_permission('view_production')
def production_list():
    productions = Production.query.all()
    return render_template('production/list.html', productions=productions)

@production_bp.route('/add', methods=['GET', 'POST'])
@login_required
@require_permission('add_workers')
def add_production():
    if request.method == 'POST':
        product_type_id = request.form.get('product_type_id')
        if not product_type_id:
            product_name = request.form.get('product_name')
            product_type = ProductType.query.filter_by(name=product_name).first()
            if not product_type:
                product_type = ProductType(name=product_name, category='أخرى')
                db.session.add(product_type)
                db.session.commit()
            product_type_id = product_type.id
        
        production = Production(
            product_type_id=product_type_id,
            location=request.form.get('location'),
            quantity=float(request.form.get('quantity', 0)),
            unit=request.form.get('unit', 'كجم'),
            date=datetime.strptime(request.form.get('date'), '%Y-%m-%d'),
            notes=request.form.get('notes')
        )
        db.session.add(production)
        db.session.commit()
        flash('تم إضافة الإنتاج بنجاح', 'success')
        return redirect(url_for('production.production_list'))
    
    product_types = ProductType.query.all()
    return render_template('production/add.html', product_types=product_types)

# ==================== Sales Routes ====================
@sales_bp.route('/')
@login_required
@require_permission('view_sales')
def sales_list():
    sales = Sales.query.all()
    return render_template('sales/list.html', sales=sales)

@sales_bp.route('/add', methods=['GET', 'POST'])
@login_required
@require_permission('add_workers')
def add_sale():
    if request.method == 'POST':
        product_type_id = request.form.get('product_type_id')
        quantity = float(request.form.get('quantity', 0))
        price_per_unit_usd = float(request.form.get('price_per_unit_usd', 0))
        price_per_unit_lbp = float(request.form.get('price_per_unit_lbp', 0))
        
        sale = Sales(
            product_type_id=product_type_id,
            quantity=quantity,
            unit=request.form.get('unit', 'كجم'),
            price_per_unit_usd=price_per_unit_usd,
            price_per_unit_lbp=price_per_unit_lbp,
            total_usd=quantity * price_per_unit_usd,
            total_lbp=quantity * price_per_unit_lbp,
            date=datetime.strptime(request.form.get('date'), '%Y-%m-%d'),
            notes=request.form.get('notes')
        )
        db.session.add(sale)
        db.session.commit()
        flash('تم إضافة عملية البيع بنجاح', 'success')
        return redirect(url_for('sales.sales_list'))
    
    product_types = ProductType.query.all()
    return render_template('sales/add.html', product_types=product_types)

# ==================== Fuel Routes ====================
@fuel_bp.route('/')
@login_required
@require_permission('view_fuel')
def fuel_list():
    fuel_logs = FuelLog.query.all()
    total_usd = sum(log.total_usd for log in fuel_logs)
    total_lbp = sum(log.total_lbp for log in fuel_logs)
    return render_template('fuel/list.html', fuel_logs=fuel_logs, total_usd=total_usd, total_lbp=total_lbp)

@fuel_bp.route('/add', methods=['GET', 'POST'])
@login_required
@require_permission('add_fuel')
def add_fuel():
    if request.method == 'POST':
        liters_str = request.form.get('liters', '0').strip()
        price_usd_str = request.form.get('price_per_liter_usd', '0').strip()
        price_lbp_str = request.form.get('price_per_liter_lbp', '0').strip()
        
        liters = float(liters_str) if liters_str else 0
        price_per_liter_usd = float(price_usd_str) if price_usd_str else 0
        price_per_liter_lbp = float(price_lbp_str) if price_lbp_str else 0
        
        fuel_log = FuelLog(
            fuel_type=request.form.get('fuel_type'),
            liters=liters,
            price_per_liter_usd=price_per_liter_usd,
            price_per_liter_lbp=price_per_liter_lbp,
            total_usd=liters * price_per_liter_usd,
            total_lbp=liters * price_per_liter_lbp,
            date=datetime.strptime(request.form.get('date'), '%Y-%m-%d'),
            notes=request.form.get('notes')
        )
        db.session.add(fuel_log)
        db.session.commit()
        flash('تم إضافة سجل الوقود بنجاح', 'success')
        return redirect(url_for('fuel.fuel_list'))
    
    return render_template('fuel/add.html')

# ==================== Medicines Routes ====================
@medicines_bp.route('/')
@login_required
@require_permission('view_medicines')
def medicines_list():
    medicines = Medicine.query.all()
    return render_template('medicines/list.html', medicines=medicines)

@medicines_bp.route('/add', methods=['GET', 'POST'])
@login_required
@require_permission('add_medicines')
def add_medicine():
    if request.method == 'POST':
        quantity_str = request.form.get('quantity', '0').strip()
        price_usd_str = request.form.get('price_usd', '0').strip()
        price_lbp_str = request.form.get('price_lbp', '0').strip()
        
        medicine = Medicine(
            name=request.form.get('name'),
            quantity=float(quantity_str) if quantity_str else 0,
            unit=request.form.get('unit', 'لتر'),
            price_usd=float(price_usd_str) if price_usd_str else 0,
            price_lbp=float(price_lbp_str) if price_lbp_str else 0,
            date=datetime.strptime(request.form.get('date'), '%Y-%m-%d'),
            notes=request.form.get('notes')
        )
        db.session.add(medicine)
        db.session.commit()
        flash('تم إضافة الدواء بنجاح', 'success')
        return redirect(url_for('medicines.medicines_list'))
    
    return render_template('medicines/add.html')

# ==================== Consumption Routes ====================
@consumption_bp.route('/')
@login_required
@require_permission('view_consumption')
def consumption_list():
    consumptions = Consumption.query.all()
    return render_template('consumption/list.html', consumptions=consumptions)

@consumption_bp.route('/add', methods=['GET', 'POST'])
@login_required
@require_permission('add_consumption')
def add_consumption():
    if request.method == 'POST':
        consumption_type = request.form.get('consumption_type')
        quantity_str = request.form.get('quantity_consumed', '0').strip()
        quantity_consumed = float(quantity_str) if quantity_str else 0
        
        consumption = Consumption(
            consumption_type=consumption_type,
            quantity_consumed=quantity_consumed,
            unit=request.form.get('unit', ''),
            date=datetime.strptime(request.form.get('date'), '%Y-%m-%d').date(),
            notes=request.form.get('notes')
        )
        
        # Link to the appropriate category
        if consumption_type == 'وقود':
            consumption.fuel_id = request.form.get('fuel_id', type=int)
        elif consumption_type == 'دواء':
            consumption.medicine_id = request.form.get('medicine_id', type=int)
        elif consumption_type == 'سماد':
            consumption.fertilizer_id = request.form.get('fertilizer_id', type=int)
        
        db.session.add(consumption)
        db.session.commit()
        flash('تم تسجيل الاستهلاك بنجاح', 'success')
        return redirect(url_for('consumption.consumption_list'))
    
    fuels = FuelLog.query.all()
    medicines = Medicine.query.all()
    fertilizers = Fertilizer.query.all()
    return render_template('consumption/add.html', fuels=fuels, medicines=medicines, fertilizers=fertilizers)

# ==================== Reports Routes ====================
@reports_bp.route('/')
@login_required
@require_permission('view_reports')
def reports_list():
    reports = Report.query.all()
    return render_template('reports/list.html', reports=reports)

@reports_bp.route('/workers')
@login_required
def workers_report():
    workers = Worker.query.all()
    return render_template('reports/workers_report.html', workers=workers)

@reports_bp.route('/production')
@login_required
def production_report():
    productions = Production.query.all()
    
    # تجميع البيانات حسب المنتج والموقع
    grouped_data = {}
    total_by_product = {}
    
    for prod in productions:
        product_name = prod.product_type.name
        location = prod.location or '-'
        category = prod.product_type.category or '-'
        
        # مفتاح التجميع: المنتج + الموقع
        key = f"{product_name}|{location}"
        
        if key not in grouped_data:
            grouped_data[key] = {
                'product_name': product_name,
                'category': category,
                'location': location,
                'quantity': 0,
                'unit': prod.unit,
                'records': []
            }
        
        grouped_data[key]['quantity'] += prod.quantity
        grouped_data[key]['records'].append(prod)
        
        # حساب الإجمالي لكل منتج
        if product_name not in total_by_product:
            total_by_product[product_name] = 0
        total_by_product[product_name] += prod.quantity
    
    # تحويل البيانات المجمعة إلى قائمة مرتبة
    grouped_list = sorted(grouped_data.values(), key=lambda x: (x['product_name'], x['location']))
    
    return render_template('reports/production_report.html', 
                         productions=productions,
                         grouped_data=grouped_list,
                         total_by_product=total_by_product)

@reports_bp.route('/sales')
@login_required
def sales_report():
    sales = Sales.query.all()
    total_usd = sum(s.total_usd for s in sales)
    total_lbp = sum(s.total_lbp for s in sales)
    return render_template('reports/sales_report.html', sales=sales, total_usd=total_usd, total_lbp=total_lbp)

@reports_bp.route('/accounting')
@login_required
def accounting_report():
    """تقرير محاسبي شامل - الإيرادات والمصروفات"""
    accounting = Accounting.query.all()
    
    # حساب الإيرادات (إيراد)
    revenues = [a for a in accounting if a.transaction_type == 'إيراد']
    revenue_usd = sum(a.amount_usd for a in revenues)
    revenue_lbp = sum(a.amount_lbp for a in revenues)
    
    # حساب المصروفات (مصروف)
    expenses = [a for a in accounting if a.transaction_type == 'مصروف']
    expenses_usd = sum(a.amount_usd for a in expenses)
    expenses_lbp = sum(a.amount_lbp for a in expenses)
    
    # حساب النتيجة الصافية
    net_usd = revenue_usd - expenses_usd
    net_lbp = revenue_lbp - expenses_lbp
    
    # تجميع حسب الفئة
    revenue_by_category = {}
    expense_by_category = {}
    
    for transaction in accounting:
        if transaction.transaction_type == 'إيراد':
            if transaction.category not in revenue_by_category:
                revenue_by_category[transaction.category] = {'usd': 0, 'lbp': 0}
            revenue_by_category[transaction.category]['usd'] += transaction.amount_usd
            revenue_by_category[transaction.category]['lbp'] += transaction.amount_lbp
        else:
            if transaction.category not in expense_by_category:
                expense_by_category[transaction.category] = {'usd': 0, 'lbp': 0}
            expense_by_category[transaction.category]['usd'] += transaction.amount_usd
            expense_by_category[transaction.category]['lbp'] += transaction.amount_lbp
    
    return render_template(
        'reports/accounting_report.html',
        accounting=accounting,
        revenues=revenues,
        expenses=expenses,
        revenue_usd=revenue_usd,
        revenue_lbp=revenue_lbp,
        expenses_usd=expenses_usd,
        expenses_lbp=expenses_lbp,
        net_usd=net_usd,
        net_lbp=net_lbp,
        revenue_by_category=revenue_by_category,
        expense_by_category=expense_by_category
    )

# ==================== Users & Permissions Routes ====================
@settings_bp.route('/users')
@login_required
def users_management():
    """إدارة المستخدمين - الإدمين فقط"""
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'danger')
        return redirect(url_for('main.index'))
    
    users = User.query.all()
    roles = Role.query.all()
    return render_template('settings/users_list.html', users=users, roles=roles)

@settings_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    """إضافة مستخدم جديد - الإدمين فقط"""
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role_id = request.form.get('role_id', type=int)
        
        if User.query.filter_by(username=username).first():
            flash('اسم المستخدم موجود بالفعل', 'danger')
            return redirect(url_for('settings.add_user'))
        
        if User.query.filter_by(email=email).first():
            flash('البريد الإلكتروني موجود بالفعل', 'danger')
            return redirect(url_for('settings.add_user'))
        
        user = User(
            username=username,
            email=email,
            role_id=role_id,
            created_by=current_user.id,
            is_active=True
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'تم إنشاء المستخدم {username} بنجاح', 'success')
        return redirect(url_for('settings.users_management'))
    
    roles = Role.query.all()
    return render_template('settings/add_user.html', roles=roles)

@settings_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """تعديل بيانات المستخدم - الإدمين فقط"""
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'danger')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.role_id = request.form.get('role_id', type=int)
        user.is_active = request.form.get('is_active') == 'on'
        user.is_admin = request.form.get('is_admin') == 'on'
        
        password = request.form.get('password')
        if password:
            user.set_password(password)
        
        db.session.commit()
        flash(f'تم تحديث بيانات {user.username} بنجاح', 'success')
        return redirect(url_for('settings.users_management'))
    
    roles = Role.query.all()
    return render_template('settings/edit_user.html', user=user, roles=roles)

@settings_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    """حذف مستخدم - الإدمين فقط"""
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'danger')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('لا يمكن حذف حسابك الخاص', 'danger')
        return redirect(url_for('settings.users_management'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    flash(f'تم حذف المستخدم {username} بنجاح', 'success')
    return redirect(url_for('settings.users_management'))

@settings_bp.route('/roles')
@login_required
def roles_management():
    """إدارة الأدوار والصلاحيات - الإدمين فقط"""
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'danger')
        return redirect(url_for('main.index'))
    
    roles = Role.query.all()
    return render_template('settings/roles_list.html', roles=roles)

@settings_bp.route('/roles/add', methods=['GET', 'POST'])
@login_required
def add_role():
    """إضافة دور جديد - الإدمين فقط"""
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        # جمع الصلاحيات المحددة
        permissions = []
        available_permissions = [
            'view_workers', 'add_workers', 'edit_workers', 'delete_workers',
            'view_attendance', 'add_attendance', 'edit_attendance',
            'view_production', 'add_production', 'edit_production', 'delete_production',
            'view_sales', 'add_sales', 'edit_sales', 'delete_sales',
            'view_accounting', 'add_accounting', 'edit_accounting',
            'view_medicines', 'add_medicines', 'edit_medicines',
            'view_fuel', 'add_fuel', 'edit_fuel',
            'view_consumption', 'add_consumption',
            'view_reports'
        ]
        
        for perm in available_permissions:
            if request.form.get(perm):
                permissions.append(perm)
        
        if not permissions:
            flash('يجب اختيار صلاحية واحدة على الأقل', 'danger')
            return redirect(url_for('settings.add_role'))
        
        role = Role(
            name=name,
            description=description,
            permissions=','.join(permissions)
        )
        
        db.session.add(role)
        db.session.commit()
        
        flash(f'تم إنشاء الدور {name} بنجاح', 'success')
        return redirect(url_for('settings.roles_management'))
    
    available_permissions = {
        'العمال': ['view_workers', 'add_workers', 'edit_workers', 'delete_workers'],
        'الحضور': ['view_attendance', 'add_attendance', 'edit_attendance'],
        'الإنتاج': ['view_production', 'add_production', 'edit_production', 'delete_production'],
        'المبيعات': ['view_sales', 'add_sales', 'edit_sales', 'delete_sales'],
        'المحاسبة': ['view_accounting', 'add_accounting', 'edit_accounting'],
        'الأدوية والأسمدة': ['view_medicines', 'add_medicines', 'edit_medicines'],
        'الوقود': ['view_fuel', 'add_fuel', 'edit_fuel'],
        'الاستهلاك': ['view_consumption', 'add_consumption'],
        'التقارير': ['view_reports']
    }
    
    return render_template('settings/add_role.html', available_permissions=available_permissions)

@settings_bp.route('/roles/<int:role_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_role(role_id):
    """تعديل دور - الإدمين فقط"""
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'danger')
        return redirect(url_for('main.index'))
    
    role = Role.query.get_or_404(role_id)
    
    if request.method == 'POST':
        role.name = request.form.get('name')
        role.description = request.form.get('description')
        
        permissions = []
        available_permissions = [
            'view_workers', 'add_workers', 'edit_workers', 'delete_workers',
            'view_attendance', 'add_attendance', 'edit_attendance',
            'view_production', 'add_production', 'edit_production', 'delete_production',
            'view_sales', 'add_sales', 'edit_sales', 'delete_sales',
            'view_accounting', 'add_accounting', 'edit_accounting',
            'view_medicines', 'add_medicines', 'edit_medicines',
            'view_fuel', 'add_fuel', 'edit_fuel',
            'view_consumption', 'add_consumption',
            'view_reports'
        ]
        
        for perm in available_permissions:
            if request.form.get(perm):
                permissions.append(perm)
        
        role.permissions = ','.join(permissions) if permissions else ''
        
        db.session.commit()
        flash(f'تم تحديث الدور {role.name} بنجاح', 'success')
        return redirect(url_for('settings.roles_management'))
    
    available_permissions = {
        'العمال': ['view_workers', 'add_workers', 'edit_workers', 'delete_workers'],
        'الحضور': ['view_attendance', 'add_attendance', 'edit_attendance'],
        'الإنتاج': ['view_production', 'add_production', 'edit_production', 'delete_production'],
        'المبيعات': ['view_sales', 'add_sales', 'edit_sales', 'delete_sales'],
        'المحاسبة': ['view_accounting', 'add_accounting', 'edit_accounting'],
        'الأدوية والأسمدة': ['view_medicines', 'add_medicines', 'edit_medicines'],
        'الوقود': ['view_fuel', 'add_fuel', 'edit_fuel'],
        'الاستهلاك': ['view_consumption', 'add_consumption'],
        'التقارير': ['view_reports']
    }
    
    current_permissions = (role.permissions or '').split(',') if role.permissions else []
    
    return render_template('settings/edit_role.html', role=role, available_permissions=available_permissions, current_permissions=current_permissions)

@settings_bp.route('/roles/<int:role_id>/delete', methods=['POST'])
@login_required
def delete_role(role_id):
    """حذف دور - الإدمين فقط"""
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'danger')
        return redirect(url_for('main.index'))
    
    role = Role.query.get_or_404(role_id)
    
    if User.query.filter_by(role_id=role_id).first():
        flash('لا يمكن حذف دور موجود به مستخدمين', 'danger')
        return redirect(url_for('settings.roles_management'))
    
    name = role.name
    db.session.delete(role)
    db.session.commit()
    
    flash(f'تم حذف الدور {name} بنجاح', 'success')
    return redirect(url_for('settings.roles_management'))

# ==================== Settings Routes ====================
@settings_bp.route('/')
@login_required
def settings():
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'danger')
        return redirect(url_for('main.index'))
    
    product_types = ProductType.query.all()
    return render_template('settings/index.html', product_types=product_types)

@settings_bp.route('/add_product_type', methods=['POST'])
@login_required
def add_product_type():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    name = request.form.get('name')
    category = request.form.get('category')
    
    if ProductType.query.filter_by(name=name).first():
        return jsonify({'error': 'المنتج موجود بالفعل'}), 400
    
    product_type = ProductType(name=name, category=category)
    db.session.add(product_type)
    db.session.commit()
    
    return jsonify({'success': True, 'id': product_type.id})

@settings_bp.route('/product_type/<int:product_type_id>', methods=['DELETE'])
@login_required
def delete_product_type(product_type_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    product_type = ProductType.query.get_or_404(product_type_id)
    db.session.delete(product_type)
    db.session.commit()
    
    return jsonify({'success': True})

# ==================== Attendance Routes ====================
@attendance_bp.route('/')
@login_required
@require_permission('view_attendance')
def attendance_list():
    """Display attendance records"""
    page = request.args.get('page', 1, type=int)
    search_worker = request.args.get('worker', '', type=str)
    search_date = request.args.get('date', '', type=str)
    
    query = Attendance.query
    
    if search_worker:
        query = query.filter(Worker.name.ilike(f'%{search_worker}%')).join(Worker)
    
    if search_date:
        try:
            search_date_obj = datetime.strptime(search_date, '%Y-%m-%d').date()
            query = query.filter(Attendance.date == search_date_obj)
        except:
            pass
    
    attendance_records = query.paginate(page=page, per_page=20)
    workers = Worker.query.all()
    
    # حساب معلومات الحسابات لكل عامل
    workers_accounts = []
    for worker in workers:
        total_advances_usd = worker.get_total_advances_usd()
        total_advances_lbp = worker.get_total_advances_lbp()
        workers_accounts.append({
            'worker': worker,
            'total_hours': worker.total_hours,
            'hourly_rate_usd': worker.hourly_rate_usd,
            'hourly_rate_lbp': worker.hourly_rate_lbp,
            'total_earnings_usd': worker.get_total_earnings_usd(),
            'total_earnings_lbp': worker.get_total_earnings_lbp(),
            'total_advances_usd': total_advances_usd,
            'total_advances_lbp': total_advances_lbp,
            'balance_usd': worker.get_balance_usd(),
            'balance_lbp': worker.get_balance_lbp()
        })
    
    # حساب إجماليات للملخص
    total_workers = len(workers_accounts)
    total_all_hours = sum(account['total_hours'] for account in workers_accounts)
    total_all_earnings_usd = sum(account['total_earnings_usd'] for account in workers_accounts)
    total_all_earnings_lbp = sum(account['total_earnings_lbp'] for account in workers_accounts)
    total_all_advances_usd = sum(account['total_advances_usd'] for account in workers_accounts)
    total_all_advances_lbp = sum(account['total_advances_lbp'] for account in workers_accounts)
    total_all_balance_usd = sum(account['balance_usd'] for account in workers_accounts)
    total_all_balance_lbp = sum(account['balance_lbp'] for account in workers_accounts)
    
    return render_template('attendance/list.html', 
                         attendance_records=attendance_records, 
                         workers=workers, 
                         workers_accounts=workers_accounts,
                         total_workers=total_workers,
                         total_all_hours=total_all_hours,
                         total_all_earnings_usd=total_all_earnings_usd,
                         total_all_earnings_lbp=total_all_earnings_lbp,
                         total_all_advances_usd=total_all_advances_usd,
                         total_all_advances_lbp=total_all_advances_lbp,
                         total_all_balance_usd=total_all_balance_usd,
                         total_all_balance_lbp=total_all_balance_lbp)

@attendance_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_attendance():
    """Add new attendance record"""
    if request.method == 'POST':
        worker_id = request.form.get('worker_id', type=int)
        att_date_str = request.form.get('date')
        att_date = datetime.strptime(att_date_str, '%Y-%m-%d').date() if att_date_str else datetime.now().date()
        status = request.form.get('status')
        check_in = request.form.get('check_in_time')
        check_out = request.form.get('check_out_time')
        hours_worked = request.form.get('hours_worked', type=float)
        notes = request.form.get('notes')
        
        # Check if attendance record already exists for this worker on this date
        existing = Attendance.query.filter_by(worker_id=worker_id, date=att_date).first()
        if existing:
            flash('تم تسجيل الحضور بالفعل لهذا العامل في هذا التاريخ', 'warning')
            return redirect(url_for('attendance.attendance_list'))
        
        attendance = Attendance(
            worker_id=worker_id,
            date=att_date,
            status=status,
            hours_worked=hours_worked or 0,
            notes=notes
        )
        
        if check_in:
            try:
                attendance.check_in_time = datetime.strptime(check_in, '%H:%M').time()
            except:
                pass
        
        if check_out:
            try:
                attendance.check_out_time = datetime.strptime(check_out, '%H:%M').time()
            except:
                pass
        
        db.session.add(attendance)
        db.session.commit()
        
        flash('تم تسجيل الحضور بنجاح', 'success')
        return redirect(url_for('attendance.attendance_list'))
    
    workers = Worker.query.all()
    return render_template('attendance/add.html', workers=workers)

@attendance_bp.route('/<int:attendance_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_attendance(attendance_id):
    """Edit attendance record"""
    attendance = Attendance.query.get_or_404(attendance_id)
    
    if request.method == 'POST':
        attendance.status = request.form.get('status')
        attendance.hours_worked = float(request.form.get('hours_worked', 0))
        attendance.notes = request.form.get('notes')
        
        check_in = request.form.get('check_in_time')
        check_out = request.form.get('check_out_time')
        
        if check_in:
            try:
                attendance.check_in_time = datetime.strptime(check_in, '%H:%M').time()
            except:
                pass
        
        if check_out:
            try:
                attendance.check_out_time = datetime.strptime(check_out, '%H:%M').time()
            except:
                pass
        
        db.session.commit()
        flash('تم تحديث سجل الحضور بنجاح', 'success')
        return redirect(url_for('attendance.attendance_list'))
    
    return render_template('attendance/edit.html', attendance=attendance)

@attendance_bp.route('/<int:attendance_id>/delete', methods=['POST'])
@login_required
def delete_attendance(attendance_id):
    """Delete attendance record"""
    attendance = Attendance.query.get_or_404(attendance_id)
    db.session.delete(attendance)
    db.session.commit()
    flash('تم حذف سجل الحضور بنجاح', 'success')
    return redirect(url_for('attendance.attendance_list'))

# ==================== Accounting Routes ====================
@accounting_bp.route('/')
@login_required
@require_permission('view_accounting')
def accounting_list():
    """Display accounting records"""
    page = request.args.get('page', 1, type=int)
    transaction_type = request.args.get('type', '', type=str)
    category = request.args.get('category', '', type=str)
    
    query = Accounting.query
    
    if transaction_type:
        query = query.filter_by(transaction_type=transaction_type)
    
    if category:
        query = query.filter_by(category=category)
    
    accounting_records = query.order_by(Accounting.date.desc()).paginate(page=page, per_page=20)
    
    # Calculate totals
    all_records = Accounting.query.all()
    total_income_usd = sum(r.amount_usd for r in all_records if r.transaction_type == 'إيراد')
    total_expense_usd = sum(r.amount_usd for r in all_records if r.transaction_type == 'مصروف')
    total_income_lbp = sum(r.amount_lbp for r in all_records if r.transaction_type == 'إيراد')
    total_expense_lbp = sum(r.amount_lbp for r in all_records if r.transaction_type == 'مصروف')
    
    return render_template('accounting/list.html', 
                         accounting_records=accounting_records,
                         total_income_usd=total_income_usd,
                         total_expense_usd=total_expense_usd,
                         total_income_lbp=total_income_lbp,
                         total_expense_lbp=total_expense_lbp)

@accounting_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_accounting():
    """Add new accounting record"""
    if request.method == 'POST':
        transaction_type = request.form.get('transaction_type')
        category = request.form.get('category')
        amount_usd_str = request.form.get('amount_usd', '0').strip()
        amount_lbp_str = request.form.get('amount_lbp', '0').strip()
        amount_usd = float(amount_usd_str) if amount_usd_str else 0
        amount_lbp = float(amount_lbp_str) if amount_lbp_str else 0
        description = request.form.get('description')
        trans_date_str = request.form.get('date')
        trans_date = datetime.strptime(trans_date_str, '%Y-%m-%d').date() if trans_date_str else datetime.now().date()
        notes = request.form.get('notes')
        
        accounting = Accounting(
            transaction_type=transaction_type,
            category=category,
            amount_usd=amount_usd,
            amount_lbp=amount_lbp,
            description=description,
            date=trans_date,
            notes=notes,
            created_by=current_user.id
        )
        
        # Link to specific department if provided
        worker_id = request.form.get('worker_id', type=int)
        if worker_id:
            accounting.worker_id = worker_id
        
        # Validate that worker is selected for advances
        if category == 'سلفة' and not worker_id:
            flash('يجب اختيار العامل عند إضافة سلفة', 'danger')
            return redirect(url_for('accounting.add_accounting'))
        
        db.session.add(accounting)
        db.session.commit()
        
        flash('تم إضافة المعاملة المحاسبية بنجاح', 'success')
        return redirect(url_for('accounting.accounting_list'))
    
    workers = Worker.query.all()
    return render_template('accounting/add.html', workers=workers)

@accounting_bp.route('/<int:accounting_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_accounting(accounting_id):
    """Edit accounting record"""
    accounting = Accounting.query.get_or_404(accounting_id)
    
    if request.method == 'POST':
        accounting.transaction_type = request.form.get('transaction_type')
        accounting.category = request.form.get('category')
        amount_usd_str = request.form.get('amount_usd', '0').strip()
        amount_lbp_str = request.form.get('amount_lbp', '0').strip()
        accounting.amount_usd = float(amount_usd_str) if amount_usd_str else 0
        accounting.amount_lbp = float(amount_lbp_str) if amount_lbp_str else 0
        accounting.description = request.form.get('description')
        date_str = request.form.get('date')
        accounting.date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.now().date()
        accounting.notes = request.form.get('notes')
        
        # Link to worker if provided
        worker_id = request.form.get('worker_id', type=int)
        accounting.worker_id = worker_id if worker_id else None
        
        # Validate that worker is selected for advances
        if accounting.category == 'سلفة' and not worker_id:
            flash('يجب اختيار العامل عند إضافة سلفة', 'danger')
            return redirect(url_for('accounting.edit_accounting', accounting_id=accounting_id))
        
        db.session.commit()
        flash('تم تحديث المعاملة المحاسبية بنجاح', 'success')
        return redirect(url_for('accounting.accounting_list'))
    
    workers = Worker.query.all()
    return render_template('accounting/edit.html', accounting=accounting, workers=workers)

@accounting_bp.route('/<int:accounting_id>/delete', methods=['POST'])
@login_required
def delete_accounting(accounting_id):
    """Delete accounting record"""
    accounting = Accounting.query.get_or_404(accounting_id)
    db.session.delete(accounting)
    db.session.commit()
    flash('تم حذف المعاملة المحاسبية بنجاح', 'success')
    return redirect(url_for('accounting.accounting_list'))

@accounting_bp.route('/report')
@login_required
def accounting_report():
    """Generate accounting report"""
    start_date = request.args.get('start_date', '', type=str)
    end_date = request.args.get('end_date', '', type=str)
    
    query = Accounting.query
    
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Accounting.date >= start_date_obj)
        except:
            pass
    
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Accounting.date <= end_date_obj)
        except:
            pass
    
    records = query.order_by(Accounting.date.desc()).all()
    
    # Calculate totals by category
    income_by_category = {}
    expense_by_category = {}
    
    for record in records:
        if record.transaction_type == 'إيراد':
            if record.category not in income_by_category:
                income_by_category[record.category] = {'usd': 0, 'lbp': 0}
            income_by_category[record.category]['usd'] += record.amount_usd
            income_by_category[record.category]['lbp'] += record.amount_lbp
        else:
            if record.category not in expense_by_category:
                expense_by_category[record.category] = {'usd': 0, 'lbp': 0}
            expense_by_category[record.category]['usd'] += record.amount_usd
            expense_by_category[record.category]['lbp'] += record.amount_lbp
    
    return render_template('accounting/report.html',
                         records=records,
                         income_by_category=income_by_category,
                         expense_by_category=expense_by_category,
                         start_date=start_date,
                         end_date=end_date)

# ==================== Admin Delete Routes ====================
# These routes allow admin to delete any record in case of errors

@settings_bp.route('/admin/delete_worker/<int:worker_id>', methods=['POST'])
@login_required
def admin_delete_worker(worker_id):
    """Admin delete worker - can delete any worker"""
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'danger')
        return redirect(url_for('main.index'))
    
    worker = Worker.query.get_or_404(worker_id)
    worker_name = worker.name
    
    # Delete all related records
    WorkShift.query.filter_by(worker_id=worker_id).delete()
    Attendance.query.filter_by(worker_id=worker_id).delete()
    
    db.session.delete(worker)
    db.session.commit()
    
    flash(f'تم حذف العامل {worker_name} وجميع سجلاته بنجاح', 'success')
    return redirect(url_for('workers.workers_list'))

@settings_bp.route('/admin/delete_attendance/<int:attendance_id>', methods=['POST'])
@login_required
def admin_delete_attendance(attendance_id):
    """Admin delete attendance record"""
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'danger')
        return redirect(url_for('main.index'))
    
    attendance = Attendance.query.get_or_404(attendance_id)
    worker_name = attendance.worker.name
    date = attendance.date
    
    db.session.delete(attendance)
    db.session.commit()
    
    flash(f'تم حذف سجل حضور {worker_name} بتاريخ {date} بنجاح', 'success')
    return redirect(url_for('attendance.attendance_list'))

@settings_bp.route('/admin/delete_production/<int:production_id>', methods=['POST'])
@login_required
def admin_delete_production(production_id):
    """Admin delete production record"""
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'danger')
        return redirect(url_for('main.index'))
    
    production = Production.query.get_or_404(production_id)
    product_name = production.product_type.name if production.product_type else 'غير محدد'
    quantity = production.quantity
    
    db.session.delete(production)
    db.session.commit()
    
    flash(f'تم حذف سجل إنتاج {product_name} - الكمية: {quantity} بنجاح', 'success')
    return redirect(url_for('production.production_list'))

@settings_bp.route('/admin/delete_sale/<int:sale_id>', methods=['POST'])
@login_required
def admin_delete_sale(sale_id):
    """Admin delete sale record"""
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'danger')
        return redirect(url_for('main.index'))
    
    sale = Sales.query.get_or_404(sale_id)
    product_name = sale.product_type.name if sale.product_type else 'غير محدد'
    total_usd = sale.total_usd
    
    db.session.delete(sale)
    db.session.commit()
    
    flash(f'تم حذف سجل مبيعات {product_name} - المبلغ: ${total_usd} بنجاح', 'success')
    return redirect(url_for('sales.sales_list'))

@settings_bp.route('/admin/delete_fuel/<int:fuel_id>', methods=['POST'])
@login_required
def admin_delete_fuel(fuel_id):
    """Admin delete fuel record"""
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'danger')
        return redirect(url_for('main.index'))
    
    fuel = FuelLog.query.get_or_404(fuel_id)
    fuel_type = fuel.fuel_type
    liters = fuel.liters
    
    db.session.delete(fuel)
    db.session.commit()
    
    flash(f'تم حذف سجل وقود {fuel_type} - الكمية: {liters} لتر بنجاح', 'success')
    return redirect(url_for('fuel.fuel_list'))

@settings_bp.route('/admin/delete_medicine/<int:medicine_id>', methods=['POST'])
@login_required
def admin_delete_medicine(medicine_id):
    """Admin delete medicine record"""
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'danger')
        return redirect(url_for('main.index'))
    
    medicine = Medicine.query.get_or_404(medicine_id)
    name = medicine.name
    quantity = medicine.quantity
    
    db.session.delete(medicine)
    db.session.commit()
    
    flash(f'تم حذف سجل دواء {name} - الكمية: {quantity} بنجاح', 'success')
    return redirect(url_for('medicines.medicines_list'))

@settings_bp.route('/admin/delete_consumption/<int:consumption_id>', methods=['POST'])
@login_required
def admin_delete_consumption(consumption_id):
    """Admin delete consumption record"""
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'danger')
        return redirect(url_for('main.index'))
    
    consumption = Consumption.query.get_or_404(consumption_id)
    consumption_type = consumption.consumption_type
    quantity = consumption.quantity_consumed
    
    db.session.delete(consumption)
    db.session.commit()
    
    flash(f'تم حذف سجل استهلاك {consumption_type} - الكمية: {quantity} بنجاح', 'success')
    return redirect(url_for('consumption.consumption_list'))

@settings_bp.route('/admin/delete_accounting/<int:accounting_id>', methods=['POST'])
@login_required
def admin_delete_accounting(accounting_id):
    """Admin delete accounting record"""
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'danger')
        return redirect(url_for('main.index'))
    
    accounting = Accounting.query.get_or_404(accounting_id)
    transaction_type = accounting.transaction_type
    amount_usd = accounting.amount_usd
    category = accounting.category
    
    db.session.delete(accounting)
    db.session.commit()
    
    flash(f'تم حذف سجل محاسبي {transaction_type} - المبلغ: ${amount_usd} - الفئة: {category} بنجاح', 'success')
    return redirect(url_for('accounting.accounting_list'))
