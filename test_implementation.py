#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
اختبار تطبيق إدارة العمال والمخزون
Test Application Implementation
"""

import sys
from datetime import datetime, date
from app import db, create_app
from app.models import Medicine, Fertilizer, FuelLog, Consumption

def test_inventory_system():
    """اختبار نظام المخزون والاستهلاك"""
    app = create_app()
    
    with app.app_context():
        print("=" * 50)
        print("اختبار نظام المخزون والاستهلاك")
        print("Testing Inventory System")
        print("=" * 50)
        
        # Test 1: Create a medicine
        print("\n1️⃣ إضافة دواء جديد...")
        medicine = Medicine(
            name="أسبرين",
            quantity=100,
            unit="قرص",
            price_usd=0.5,
            price_lbp=15000,
            date=date.today()
        )
        db.session.add(medicine)
        db.session.commit()
        print(f"✅ تم إضافة الدواء: {medicine.name}")
        print(f"   الكمية الأولية: {medicine.quantity} {medicine.unit}")
        print(f"   السعر: ${medicine.price_usd} / {medicine.price_lbp} ل.ل")
        print(f"   القيمة الإجمالية: ${medicine.get_total_value_usd():.2f}")
        
        # Test 2: Create consumption records
        print("\n2️⃣ تسجيل استهلاك من الدواء...")
        consumption1 = Consumption(
            consumption_type='دواء',
            medicine_id=medicine.id,
            quantity_consumed=10,
            unit='قرص',
            date=date.today(),
            notes='استهلاك في الصباح'
        )
        db.session.add(consumption1)
        db.session.commit()
        print(f"✅ تم تسجيل استهلاك: {consumption1.quantity_consumed} {consumption1.unit}")
        print(f"   الكمية المتبقية: {medicine.get_remaining_quantity():.2f} {medicine.unit}")
        
        # Test 3: Add more consumption
        print("\n3️⃣ تسجيل استهلاك إضافي...")
        consumption2 = Consumption(
            consumption_type='دواء',
            medicine_id=medicine.id,
            quantity_consumed=30,
            unit='قرص',
            date=date.today(),
            notes='استهلاك في المساء'
        )
        db.session.add(consumption2)
        db.session.commit()
        print(f"✅ تم تسجيل استهلاك إضافي: {consumption2.quantity_consumed} {consumption2.unit}")
        print(f"   إجمالي الاستهلاك: {consumption1.quantity_consumed + consumption2.quantity_consumed} {consumption2.unit}")
        print(f"   الكمية المتبقية: {medicine.get_remaining_quantity():.2f} {medicine.unit}")
        
        # Test 4: Test with Fertilizer
        print("\n4️⃣ اختبار مع السماد...")
        fertilizer = Fertilizer(
            name="سماد الدجاج",
            quantity=500,
            unit="كجم",
            price_usd=2.0,
            price_lbp=60000,
            date=date.today()
        )
        db.session.add(fertilizer)
        db.session.commit()
        print(f"✅ تم إضافة سماد: {fertilizer.name}")
        print(f"   الكمية الأولية: {fertilizer.quantity} {fertilizer.unit}")
        print(f"   القيمة الإجمالية: ${fertilizer.get_total_value_usd():.2f}")
        
        # Add consumption to fertilizer
        fert_consumption = Consumption(
            consumption_type='سماد',
            fertilizer_id=fertilizer.id,
            quantity_consumed=100,
            unit='كجم',
            date=date.today(),
            notes='استخدام في الحقل الشمالي'
        )
        db.session.add(fert_consumption)
        db.session.commit()
        print(f"✅ تم تسجيل استهلاك السماد: {fert_consumption.quantity_consumed} {fert_consumption.unit}")
        print(f"   الكمية المتبقية: {fertilizer.get_remaining_quantity():.2f} {fertilizer.unit}")
        
        # Test 5: Test with Fuel
        print("\n5️⃣ اختبار مع الوقود...")
        fuel = FuelLog(
            fuel_type="مازوت",
            liters=1000,
            price_per_liter_usd=1.5,
            price_per_liter_lbp=45000,
            date=date.today()
        )
        db.session.add(fuel)
        db.session.commit()
        print(f"✅ تم إضافة وقود: {fuel.fuel_type}")
        print(f"   الكمية الأولية: {fuel.liters} لتر")
        
        # Add consumption to fuel
        fuel_consumption = Consumption(
            consumption_type='وقود',
            fuel_id=fuel.id,
            quantity_consumed=100,
            unit='لتر',
            date=date.today(),
            notes='استهلاك في الضخ'
        )
        db.session.add(fuel_consumption)
        db.session.commit()
        print(f"✅ تم تسجيل استهلاك الوقود: {fuel_consumption.quantity_consumed} {fuel_consumption.unit}")
        print(f"   الكمية المتبقية: {fuel.get_remaining_quantity():.2f} {fuel.unit}")
        
        # Summary Report
        print("\n" + "=" * 50)
        print("📊 تقرير الملخص | SUMMARY REPORT")
        print("=" * 50)
        
        all_medicines = Medicine.query.all()
        all_fertilizers = Fertilizer.query.all()
        all_fuels = FuelLog.query.all()
        
        print(f"\n📋 الأدوية والمبيدات:")
        for med in all_medicines:
            remaining = med.get_remaining_quantity()
            status = "✅ متوفر" if remaining > 0 else "⚠️ نفذ" if remaining == 0 else "❌ ناقص"
            print(f"   • {med.name}: {remaining:.2f}/{med.quantity} {med.unit} {status}")
            print(f"     القيمة الإجمالية: ${med.get_total_value_usd():.2f}")
        
        print(f"\n📋 الأسمدة:")
        for fert in all_fertilizers:
            remaining = fert.get_remaining_quantity()
            status = "✅ متوفر" if remaining > 0 else "⚠️ نفذ" if remaining == 0 else "❌ ناقص"
            print(f"   • {fert.name}: {remaining:.2f}/{fert.quantity} {fert.unit} {status}")
            print(f"     القيمة الإجمالية: ${fert.get_total_value_usd():.2f}")
        
        print(f"\n📋 الوقود:")
        for f in all_fuels:
            remaining = f.get_remaining_quantity()
            status = "✅ متوفر" if remaining > 0 else "⚠️ نفذ" if remaining == 0 else "❌ ناقص"
            print(f"   • {f.fuel_type}: {remaining:.2f}/{f.liters} لتر {status}")
        
        print("\n" + "=" * 50)
        print("✅ اكتمل الاختبار بنجاح!")
        print("=" * 50)

if __name__ == '__main__':
    try:
        test_inventory_system()
    except Exception as e:
        print(f"\n❌ خطأ: {str(e)}")
        import traceback
        traceback.print_exc()
