#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Create Admin User Script
إنشاء حساب الإدمين
"""

import os
import sys
from app import create_app, db
from app.models import User, Role

def create_admin():
    """Create admin user"""
    app = create_app()
    
    with app.app_context():
        print("=" * 50)
        print("🔐 إنشاء حساب الإدمين")
        print("=" * 50)
        
        # Get input from user
        username = input("\n📝 اسم المستخدم: ").strip()
        if not username:
            print("❌ اسم المستخدم مطلوب!")
            return
        
        email = input("📧 البريد الإلكتروني: ").strip()
        if not email:
            print("❌ البريد الإلكتروني مطلوب!")
            return
        
        password = input("🔑 كلمة المرور: ").strip()
        if not password:
            print("❌ كلمة المرور مطلوبة!")
            return
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            print("❌ اسم المستخدم موجود بالفعل!")
            return
        
        if User.query.filter_by(email=email).first():
            print("❌ البريد الإلكتروني موجود بالفعل!")
            return
        
        # Create admin user
        admin = User(
            username=username,
            email=email,
            is_admin=True,
            is_active=True
        )
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.commit()
        
        print("\n" + "=" * 50)
        print("✅ تم إنشاء حساب الإدمين بنجاح!")
        print("=" * 50)
        print(f"📝 اسم المستخدم: {username}")
        print(f"📧 البريد الإلكتروني: {email}")
        print(f"🔐 الحالة: مسؤول النظام ✓")
        print("=" * 50)
        print("\n🌐 يمكنك الآن تسجيل الدخول من:")
        print("   http://localhost:5001")
        print("\n")

if __name__ == '__main__':
    create_admin()
