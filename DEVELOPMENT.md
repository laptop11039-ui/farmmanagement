# 💻 دليل التطوير والصيانة

## تغيير كلمة مرور المسؤول

```python
from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    admin.set_password('كلمة_المرور_الجديدة')
    db.session.commit()
    print('تم تغيير كلمة المرور بنجاح')
```

## إضافة مستخدم جديد

```python
from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    user = User(username='newuser', email='user@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    print('تم إضافة المستخدم الجديد')
```

## مسح قاعدة البيانات

```python
from app import create_app, db

app = create_app()
with app.app_context():
    db.drop_all()
    db.create_all()
    print('تم مسح قاعدة البيانات وإعادة تهيئتها')
```

## إضافة أصناف منتجات افتراضية

```python
from app import create_app, db
from app.models import ProductType

products = [
    ('رومستار', 'دراق'),
    ('ديومندري', 'دراق'),
    ('أوريون', 'دراق'),
    ('ريدشليده', 'دراق'),
    ('سارويال', 'دراق'),
    ('رين صن', 'دراق'),
    ('فيري كود', 'دراق'),
    ('تفاح أحمر', 'تفاح'),
    ('تفاح أبيض', 'تفاح'),
    ('خيار', 'خضروات'),
    ('طماطم', 'خضروات'),
    ('باذنجان', 'خضروات'),
]

app = create_app()
with app.app_context():
    for name, category in products:
        if not ProductType.query.filter_by(name=name).first():
            pt = ProductType(name=name, category=category)
            db.session.add(pt)
    db.session.commit()
    print('تم إضافة الأصناف')
```

## تصدير البيانات

```python
import csv
from app import create_app
from app.models import Worker, Sales, FuelLog

app = create_app()
with app.app_context():
    # تصدير العمال
    workers = Worker.query.all()
    with open('workers.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['الاسم', 'الهاتف', 'سعر الساعة', 'إجمالي الساعات'])
        for w in workers:
            writer.writerow([w.name, w.phone, w.hourly_rate_usd, w.total_hours])
    print('تم تصدير العمال')
```

## تشغيل على منفذ مختلف

```python
# في run.py أو من terminal
python run.py
# ثم غيّر HOST و PORT
```

أو من terminal مباشرة:
```bash
FLASK_APP=run.py FLASK_ENV=development python -m flask run --port 5001
```

## تفعيل وضع الإنتاج

```bash
set FLASK_ENV=production
set FLASK_APP=run.py
python -m flask run
```

## استخدام قاعدة بيانات PostgreSQL

1. غيّر DATABASE_URL في .env:
```
DATABASE_URL=postgresql://user:password@localhost/worker_db
```

2. ثبّت مكتبة psycopg2:
```bash
pip install psycopg2-binary
```

## النسخ الاحتياطية

```python
import shutil
from datetime import datetime

# نسخ قاعدة البيانات
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy('worker_management.db', f'backup_worker_management_{timestamp}.db')
print(f'تم النسخ الاحتياطي: backup_worker_management_{timestamp}.db')
```

## معلومات مفيدة

### هيكل البيانات الرئيسي
```
Worker
├── WorkShift (نوبات العمل)
│   └── ProductType (نوع المنتج)
│
Sales
├── ProductType
│
Production
├── ProductType
│
FuelLog
Medicine
Fertilizer
Consumption
├── ProductType
```

### المسارات الرئيسية
```
/                           - الصفحة الرئيسية
/auth/login                - تسجيل الدخول
/auth/register             - التسجيل
/workers/                  - قائمة العمال
/workers/<id>              - تفاصيل العامل
/workers/<id>/add_shift    - إضافة نوبة
/production/               - الإنتاج
/sales/                    - المبيعات
/fuel/                     - الوقود
/medicines/                - الأدوية
/consumption/              - الاستهلاك
/reports/                  - التقارير
/settings/                 - الإعدادات
```

### الأوامر المفيدة

```bash
# تشغيل بدون قاعدة بيانات جديدة
python run.py

# الدخول إلى shell
flask shell

# عرض جميع المسارات
flask routes

# تشغيل الاختبارات
python test_installation.py
```

## التصحيح والتطوير

### تفعيل debug mode
```python
# في run.py
if __name__ == '__main__':
    app.run(debug=True)
```

### إضافة logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
```

## نصائح الأداء

1. استخدم indexes في قاعدة البيانات:
```python
class Worker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), index=True)  # إضافة index
```

2. استخدم pagination للقوائم الطويلة:
```python
page = request.args.get('page', 1, type=int)
workers = Worker.query.paginate(page=page, per_page=10)
```

3. cache البيانات الثابتة:
```python
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
```

---

**استمتع بالتطوير!** 🚀
