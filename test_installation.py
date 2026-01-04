"""
Script for testing the application
تم التحقق من أن جميع المتطلبات مثبتة بشكل صحيح
"""

import sys
from pathlib import Path

def check_requirements():
    """Check if all required packages are installed"""
    print("🔍 جاري فحص المتطلبات...")
    
    requirements = {
        'Flask': 'Flask',
        'Flask-SQLAlchemy': 'flask_sqlalchemy',
        'Flask-Login': 'flask_login',
        'Werkzeug': 'werkzeug',
    }
    
    failed = []
    for name, package in requirements.items():
        try:
            __import__(package)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name}")
            failed.append(name)
    
    return len(failed) == 0

def check_project_structure():
    """Check if all required files and folders exist"""
    print("\n🔍 جاري فحص هيكل المشروع...")
    
    required_files = [
        'config.py',
        'run.py',
        'requirements.txt',
        'README.md',
        'app/__init__.py',
        'app/models.py',
        'app/routes.py',
        'app/static/css/style.css',
        'app/static/js/main.js',
        'app/templates/base.html',
        'app/templates/dashboard.html',
    ]
    
    project_root = Path(__file__).parent
    failed = []
    
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            failed.append(file_path)
    
    return len(failed) == 0

def test_app_creation():
    """Test if the app can be created"""
    print("\n🔍 جاري اختبار إنشاء التطبيق...")
    
    try:
        from app import create_app
        app = create_app('testing')
        print("✅ تم إنشاء التطبيق بنجاح")
        
        with app.test_client() as client:
            # Test if the app responds
            response = client.get('/')
            if response.status_code in [200, 302]:  # 302 for redirect to login
                print("✅ التطبيق يستجيب بشكل صحيح")
                return True
            else:
                print(f"❌ خطأ في الاستجابة: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ خطأ في إنشاء التطبيق: {e}")
        return False

def main():
    print("=" * 50)
    print("🧪 اختبار تطبيق إدارة المزرعة والعمال")
    print("=" * 50 + "\n")
    
    req_ok = check_requirements()
    struct_ok = check_project_structure()
    app_ok = test_app_creation()
    
    print("\n" + "=" * 50)
    print("📊 نتائج الاختبار:")
    print("=" * 50)
    
    results = {
        'المتطلبات': req_ok,
        'هيكل المشروع': struct_ok,
        'التطبيق': app_ok,
    }
    
    all_ok = all(results.values())
    
    for test_name, result in results.items():
        status = "✅ نجح" if result else "❌ فشل"
        print(f"{test_name}: {status}")
    
    print("=" * 50)
    
    if all_ok:
        print("\n🎉 جميع الاختبارات نجحت! النظام جاهز للاستخدام")
        print("\nلتشغيل التطبيق:")
        print("  python run.py")
        return 0
    else:
        print("\n⚠️  بعض الاختبارات فشلت. يرجى التحقق من الأخطاء أعلاه")
        return 1

if __name__ == '__main__':
    sys.exit(main())
