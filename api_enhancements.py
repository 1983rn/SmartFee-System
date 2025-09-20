"""
API Enhancements for SmartFee Revenue Collection System
This file contains additional API endpoints to complete the functionality
"""

from flask import jsonify, request, session
from datetime import datetime, timedelta
import csv
import io
from sqlalchemy import func, and_, or_

# These functions should be added to your main app.py file

def add_enhanced_api_endpoints(app, db, Student, Income, Expenditure, login_required, get_school_filtered_query, get_current_school_id):
    """
    Add enhanced API endpoints to the Flask app
    """
    
    @app.route('/api/student/<student_id>/details')
    @login_required
    def api_get_student_details(student_id):
        """Get detailed information about a specific student"""
        try:
            # Get school-filtered student
            student_query = get_school_filtered_query(Student)
            student = student_query.filter_by(student_id=student_id).first()
            
            if not student:
                return jsonify({'error': 'Student not found'}), 404
            
            # Get payment history
            current_school_id = get_current_school_id()
            if current_school_id:
                payments = Income.query.filter_by(
                    school_id=current_school_id,
                    student_id=student_id
                ).order_by(Income.payment_date.desc()).all()
            else:
                payments = Income.query.filter_by(student_id=student_id).order_by(Income.payment_date.desc()).all()
            
            payment_history = []
            for payment in payments:
                payment_history.append({
                    'date': payment.payment_date.strftime('%Y-%m-%d'),
                    'amount': float(payment.amount_paid),
                    'fund_type': payment.fund_type,
                    'payment_method': getattr(payment, 'payment_method', 'Cash'),
                    'receipt_number': getattr(payment, 'receipt_number', 'N/A')
                })
            
            student_data = {
                'student_id': student.decrypted_student_id,
                'name': student.decrypted_name,
                'sex': student.decrypted_sex,
                'form_class': student.decrypted_form_class,
                'parent_phone': student.decrypted_parent_phone,
                'pta_required': float(student.pta_amount_required or 0),
                'pta_paid': float(student.pta_amount_paid or 0),
                'pta_balance': float(student.get_pta_balance()),
                'sdf_required': float(student.sdf_amount_required or 0),
                'sdf_paid': float(student.sdf_amount_paid or 0),
                'sdf_balance': float(student.get_sdf_balance()),
                'boarding_required': float(student.boarding_amount_required or 0),
                'boarding_paid': float(student.boarding_amount_paid or 0),
                'boarding_balance': float(student.get_boarding_balance()),
                'total_required': float((student.pta_amount_required or 0) + (student.sdf_amount_required or 0) + (student.boarding_amount_required or 0)),
                'total_paid': float((student.pta_amount_paid or 0) + (student.sdf_amount_paid or 0) + (student.boarding_amount_paid or 0)),
                'total_balance': float(student.get_pta_balance() + student.get_sdf_balance() + student.get_boarding_balance()),
                'is_paid_in_full': student.is_paid_in_full(),
                'payment_history': payment_history,
                'last_payment_date': payments[0].payment_date.strftime('%Y-%m-%d') if payments else None
            }
            
            return jsonify(student_data)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/students/search')
    @login_required
    def api_search_students():
        """Advanced student search API"""
        try:
            # Get search parameters
            query = request.args.get('q', '').strip()
            form_class = request.args.get('class', '').strip()
            payment_status = request.args.get('status', '').strip()  # 'paid', 'outstanding', 'partial'
            sex = request.args.get('sex', '').strip()
            limit = int(request.args.get('limit', 50))
            
            # Start with school-filtered query
            student_query = get_school_filtered_query(Student)
            
            # Apply filters
            if query:
                # Search in name and student_id (you may need to adjust based on encryption)
                student_query = student_query.filter(
                    or_(
                        Student.name.contains(query),
                        Student.student_id.contains(query)
                    )
                )
            
            if form_class:
                student_query = student_query.filter(Student.form_class.contains(form_class))
            
            if sex:
                student_query = student_query.filter(Student.sex == sex)
            
            students = student_query.limit(limit).all()
            
            # Filter by payment status if specified
            if payment_status:
                if payment_status == 'paid':
                    students = [s for s in students if s.is_paid_in_full()]
                elif payment_status == 'outstanding':
                    students = [s for s in students if not s.is_paid_in_full()]
                elif payment_status == 'partial':
                    students = [s for s in students if not s.is_paid_in_full() and (s.pta_amount_paid > 0 or s.sdf_amount_paid > 0 or s.boarding_amount_paid > 0)]
            
            # Format results
            results = []
            for student in students:
                results.append({
                    'id': student.id,
                    'student_id': student.decrypted_student_id,
                    'name': student.decrypted_name,
                    'sex': student.decrypted_sex,
                    'form_class': student.decrypted_form_class,
                    'total_paid': float((student.pta_amount_paid or 0) + (student.sdf_amount_paid or 0) + (student.boarding_amount_paid or 0)),
                    'total_balance': float(student.get_pta_balance() + student.get_sdf_balance() + student.get_boarding_balance()),
                    'is_paid_in_full': student.is_paid_in_full(),
                    'parent_phone': student.decrypted_parent_phone
                })
            
            return jsonify({
                'students': results,
                'total': len(results),
                'query': query
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/analytics/financial-overview')
    @login_required
    def api_financial_overview():
        """Get financial analytics data for charts"""
        try:
            current_school_id = get_current_school_id()
            
            # Get date range (default to last 30 days)
            days = int(request.args.get('days', 30))
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Daily income and expenditure
            daily_data = []
            current_date = start_date
            
            while current_date <= end_date:
                if current_school_id:
                    daily_income = db.session.query(func.sum(Income.amount_paid)).filter(
                        Income.school_id == current_school_id,
                        Income.payment_date == current_date
                    ).scalar() or 0
                    
                    daily_expenditure = db.session.query(func.sum(Expenditure.amount_paid)).filter(
                        Expenditure.school_id == current_school_id,
                        Expenditure.date == current_date
                    ).scalar() or 0
                else:
                    daily_income = db.session.query(func.sum(Income.amount_paid)).filter(
                        Income.payment_date == current_date
                    ).scalar() or 0
                    
                    daily_expenditure = db.session.query(func.sum(Expenditure.amount_paid)).filter(
                        Expenditure.date == current_date
                    ).scalar() or 0
                
                daily_data.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'income': float(daily_income),
                    'expenditure': float(daily_expenditure),
                    'net': float(daily_income - daily_expenditure)
                })
                
                current_date += timedelta(days=1)
            
            # Fund type breakdown
            if current_school_id:
                pta_total = db.session.query(func.sum(Income.amount_paid)).filter(
                    Income.school_id == current_school_id,
                    Income.fund_type == 'PTA'
                ).scalar() or 0
                
                sdf_total = db.session.query(func.sum(Income.amount_paid)).filter(
                    Income.school_id == current_school_id,
                    Income.fund_type == 'SDF'
                ).scalar() or 0
                
                boarding_total = db.session.query(func.sum(Income.amount_paid)).filter(
                    Income.school_id == current_school_id,
                    Income.fund_type == 'Boarding'
                ).scalar() or 0
            else:
                pta_total = db.session.query(func.sum(Income.amount_paid)).filter(
                    Income.fund_type == 'PTA'
                ).scalar() or 0
                
                sdf_total = db.session.query(func.sum(Income.amount_paid)).filter(
                    Income.fund_type == 'SDF'
                ).scalar() or 0
                
                boarding_total = db.session.query(func.sum(Income.amount_paid)).filter(
                    Income.fund_type == 'Boarding'
                ).scalar() or 0
            
            fund_breakdown = {
                'PTA': float(pta_total),
                'SDF': float(sdf_total),
                'Boarding': float(boarding_total)
            }
            
            return jsonify({
                'daily_data': daily_data,
                'fund_breakdown': fund_breakdown,
                'period': f'{start_date} to {end_date}'
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/export/students')
    @login_required
    def api_export_students():
        """Export students data as CSV"""
        try:
            format_type = request.args.get('format', 'csv').lower()
            
            # Get school-filtered students
            students = get_school_filtered_query(Student).all()
            
            if format_type == 'csv':
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write header
                writer.writerow([
                    'Student ID', 'Name', 'Sex', 'Form/Class', 'Parent Phone',
                    'PTA Required', 'PTA Paid', 'PTA Balance',
                    'SDF Required', 'SDF Paid', 'SDF Balance',
                    'Boarding Required', 'Boarding Paid', 'Boarding Balance',
                    'Total Required', 'Total Paid', 'Total Balance',
                    'Payment Status'
                ])
                
                # Write data
                for student in students:
                    writer.writerow([
                        student.decrypted_student_id,
                        student.decrypted_name,
                        student.decrypted_sex,
                        student.decrypted_form_class,
                        student.decrypted_parent_phone or '',
                        student.pta_amount_required or 0,
                        student.pta_amount_paid or 0,
                        student.get_pta_balance(),
                        student.sdf_amount_required or 0,
                        student.sdf_amount_paid or 0,
                        student.get_sdf_balance(),
                        student.boarding_amount_required or 0,
                        student.boarding_amount_paid or 0,
                        student.get_boarding_balance(),
                        (student.pta_amount_required or 0) + (student.sdf_amount_required or 0) + (student.boarding_amount_required or 0),
                        (student.pta_amount_paid or 0) + (student.sdf_amount_paid or 0) + (student.boarding_amount_paid or 0),
                        student.get_pta_balance() + student.get_sdf_balance() + student.get_boarding_balance(),
                        'Paid in Full' if student.is_paid_in_full() else 'Outstanding'
                    ])
                
                return jsonify({
                    'data': output.getvalue(),
                    'filename': f'students_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                    'content_type': 'text/csv'
                })
            
            else:
                return jsonify({'error': 'Unsupported format'}), 400
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/dashboard/stats')
    @login_required
    def api_dashboard_stats():
        """Get real-time dashboard statistics"""
        try:
            current_school_id = get_current_school_id()
            
            # Get all students for the school
            students = get_school_filtered_query(Student).all()
            
            # Calculate statistics
            total_students = len(students)
            paid_in_full = len([s for s in students if s.is_paid_in_full()])
            outstanding = total_students - paid_in_full
            
            # Today's financial data
            today = datetime.now().date()
            if current_school_id:
                today_income = db.session.query(func.sum(Income.amount_paid)).filter(
                    Income.school_id == current_school_id,
                    Income.payment_date == today
                ).scalar() or 0
                
                today_expenditure = db.session.query(func.sum(Expenditure.amount_paid)).filter(
                    Expenditure.school_id == current_school_id,
                    Expenditure.date == today
                ).scalar() or 0
            else:
                today_income = db.session.query(func.sum(Income.amount_paid)).filter(
                    Income.payment_date == today
                ).scalar() or 0
                
                today_expenditure = db.session.query(func.sum(Expenditure.amount_paid)).filter(
                    Expenditure.date == today
                ).scalar() or 0
            
            # Total outstanding amount
            total_outstanding_amount = sum([
                s.get_pta_balance() + s.get_sdf_balance() + s.get_boarding_balance()
                for s in students if not s.is_paid_in_full()
            ])
            
            return jsonify({
                'total_students': total_students,
                'paid_in_full': paid_in_full,
                'outstanding_count': outstanding,
                'today_income': float(today_income),
                'today_expenditure': float(today_expenditure),
                'today_net': float(today_income - today_expenditure),
                'total_outstanding_amount': float(total_outstanding_amount),
                'payment_completion_rate': round((paid_in_full / total_students * 100) if total_students > 0 else 0, 1),
                'last_updated': datetime.now().isoformat()
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/notifications/outstanding-students')
    @login_required
    def api_outstanding_students():
        """Get list of students with outstanding payments for notifications"""
        try:
            students = get_school_filtered_query(Student).all()
            outstanding_students = []
            
            for student in students:
                if not student.is_paid_in_full():
                    total_outstanding = student.get_pta_balance() + student.get_sdf_balance() + student.get_boarding_balance()
                    
                    outstanding_students.append({
                        'id': student.id,
                        'student_id': student.decrypted_student_id,
                        'name': student.decrypted_name,
                        'parent_phone': student.decrypted_parent_phone,
                        'form_class': student.decrypted_form_class,
                        'pta_balance': float(student.get_pta_balance()),
                        'sdf_balance': float(student.get_sdf_balance()),
                        'boarding_balance': float(student.get_boarding_balance()),
                        'total_outstanding': float(total_outstanding),
                        'has_phone': bool(student.decrypted_parent_phone and student.decrypted_parent_phone.strip())
                    })
            
            # Sort by total outstanding amount (highest first)
            outstanding_students.sort(key=lambda x: x['total_outstanding'], reverse=True)
            
            return jsonify({
                'students': outstanding_students,
                'total_count': len(outstanding_students),
                'students_with_phone': len([s for s in outstanding_students if s['has_phone']]),
                'total_outstanding_amount': sum([s['total_outstanding'] for s in outstanding_students])
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return app