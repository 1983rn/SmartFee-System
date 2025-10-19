"""
Enhanced Financial Analytics API Endpoints
Add these endpoints to your main app.py file
"""

from flask import jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import func, extract, and_
from collections import defaultdict
import calendar

def add_financial_analytics_endpoints(app, db, Student, Income, Expenditure, login_required, get_school_filtered_query, get_current_school_id):
    """
    Add enhanced financial analytics API endpoints
    """
    
    @app.route('/api/analytics/monthly-trends')
    @login_required
    def api_monthly_trends():
        """Get monthly financial trends for the past 12 months"""
        try:
            current_school_id = get_current_school_id()
            
            # Get date range for past 12 months
            end_date = datetime.now().date()
            start_date = end_date.replace(day=1) - timedelta(days=365)
            
            monthly_data = []
            current_month = start_date.replace(day=1)
            
            while current_month <= end_date:
                month_start = current_month
                if current_month.month == 12:
                    month_end = current_month.replace(year=current_month.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    month_end = current_month.replace(month=current_month.month + 1, day=1) - timedelta(days=1)
                
                # Get monthly income
                if current_school_id:
                    monthly_income = db.session.query(func.sum(Income.amount_paid)).filter(
                        Income.school_id == current_school_id,
                        Income.payment_date >= month_start,
                        Income.payment_date <= month_end
                    ).scalar() or 0
                    
                    monthly_expenditure = db.session.query(func.sum(Expenditure.amount_paid)).filter(
                        Expenditure.school_id == current_school_id,
                        Expenditure.date >= month_start,
                        Expenditure.date <= month_end
                    ).scalar() or 0
                else:
                    monthly_income = db.session.query(func.sum(Income.amount_paid)).filter(
                        Income.payment_date >= month_start,
                        Income.payment_date <= month_end
                    ).scalar() or 0
                    
                    monthly_expenditure = db.session.query(func.sum(Expenditure.amount_paid)).filter(
                        Expenditure.date >= month_start,
                        Expenditure.date <= month_end
                    ).scalar() or 0
                
                monthly_data.append({
                    'month': current_month.strftime('%Y-%m'),
                    'month_name': calendar.month_name[current_month.month],
                    'year': current_month.year,
                    'income': float(monthly_income),
                    'expenditure': float(monthly_expenditure),
                    'net': float(monthly_income - monthly_expenditure)
                })
                
                # Move to next month
                if current_month.month == 12:
                    current_month = current_month.replace(year=current_month.year + 1, month=1)
                else:
                    current_month = current_month.replace(month=current_month.month + 1)
            
            return jsonify({
                'monthly_trends': monthly_data,
                'period': f'{start_date} to {end_date}'
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/analytics/payment-patterns')
    @login_required
    def api_payment_patterns():
        """Analyze payment patterns and trends"""
        try:
            current_school_id = get_current_school_id()
            
            # Get payment patterns by day of week
            if current_school_id:
                payments = Income.query.filter_by(school_id=current_school_id).all()
            else:
                payments = Income.query.all()
            
            # Day of week analysis
            day_patterns = defaultdict(lambda: {'count': 0, 'amount': 0})
            for payment in payments:
                day_name = payment.payment_date.strftime('%A')
                day_patterns[day_name]['count'] += 1
                day_patterns[day_name]['amount'] += float(payment.amount_paid)
            
            # Fund type analysis
            fund_patterns = defaultdict(lambda: {'count': 0, 'amount': 0})
            for payment in payments:
                fund_patterns[payment.fund_type]['count'] += 1
                fund_patterns[payment.fund_type]['amount'] += float(payment.amount_paid)
            
            # Payment size distribution
            payment_ranges = {
                '0-1000': {'count': 0, 'amount': 0},
                '1001-5000': {'count': 0, 'amount': 0},
                '5001-10000': {'count': 0, 'amount': 0},
                '10001-20000': {'count': 0, 'amount': 0},
                '20000+': {'count': 0, 'amount': 0}
            }
            
            for payment in payments:
                amount = float(payment.amount_paid)
                if amount <= 1000:
                    payment_ranges['0-1000']['count'] += 1
                    payment_ranges['0-1000']['amount'] += amount
                elif amount <= 5000:
                    payment_ranges['1001-5000']['count'] += 1
                    payment_ranges['1001-5000']['amount'] += amount
                elif amount <= 10000:
                    payment_ranges['5001-10000']['count'] += 1
                    payment_ranges['5001-10000']['amount'] += amount
                elif amount <= 20000:
                    payment_ranges['10001-20000']['count'] += 1
                    payment_ranges['10001-20000']['amount'] += amount
                else:
                    payment_ranges['20000+']['count'] += 1
                    payment_ranges['20000+']['amount'] += amount
            
            return jsonify({
                'day_patterns': dict(day_patterns),
                'fund_patterns': dict(fund_patterns),
                'payment_ranges': payment_ranges,
                'total_payments': len(payments)
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/analytics/collection-efficiency')
    @login_required
    def api_collection_efficiency():
        """Analyze fee collection efficiency"""
        try:
            students = get_school_filtered_query(Student).all()
            
            if not students:
                return jsonify({
                    'total_students': 0,
                    'collection_rate': 0,
                    'efficiency_metrics': {}
                })
            
            # Calculate collection metrics
            total_students = len(students)
            paid_in_full = len([s for s in students if s.is_paid_in_full()])
            partial_payments = len([s for s in students if not s.is_paid_in_full() and 
                                  ((s.pta_amount_paid or 0) > 0 or (s.sdf_amount_paid or 0) > 0 or (s.boarding_amount_paid or 0) > 0)])
            no_payments = total_students - paid_in_full - partial_payments
            
            # Calculate total amounts
            total_required = sum([
                (s.pta_amount_required or 0) + (s.sdf_amount_required or 0) + (s.boarding_amount_required or 0)
                for s in students
            ])
            
            total_collected = sum([
                (s.pta_amount_paid or 0) + (s.sdf_amount_paid or 0) + (s.boarding_amount_paid or 0)
                for s in students
            ])
            
            total_outstanding = total_required - total_collected
            
            # Fund-wise analysis
            fund_analysis = {
                'PTA': {
                    'required': sum([(s.pta_amount_required or 0) for s in students]),
                    'collected': sum([(s.pta_amount_paid or 0) for s in students]),
                    'outstanding': sum([s.get_pta_balance() for s in students])
                },
                'SDF': {
                    'required': sum([(s.sdf_amount_required or 0) for s in students]),
                    'collected': sum([(s.sdf_amount_paid or 0) for s in students]),
                    'outstanding': sum([s.get_sdf_balance() for s in students])
                },
                'Boarding': {
                    'required': sum([(s.boarding_amount_required or 0) for s in students]),
                    'collected': sum([(s.boarding_amount_paid or 0) for s in students]),
                    'outstanding': sum([s.get_boarding_balance() for s in students])
                }
            }
            
            # Calculate collection rates
            for fund in fund_analysis:
                if fund_analysis[fund]['required'] > 0:
                    fund_analysis[fund]['collection_rate'] = round(
                        (fund_analysis[fund]['collected'] / fund_analysis[fund]['required']) * 100, 2
                    )
                else:
                    fund_analysis[fund]['collection_rate'] = 0
            
            # Class-wise analysis
            class_analysis = defaultdict(lambda: {
                'total_students': 0,
                'paid_in_full': 0,
                'partial_payments': 0,
                'no_payments': 0,
                'total_required': 0,
                'total_collected': 0
            })
            
            for student in students:
                class_name = student.decrypted_form_class
                class_analysis[class_name]['total_students'] += 1
                
                if student.is_paid_in_full():
                    class_analysis[class_name]['paid_in_full'] += 1
                elif (student.pta_amount_paid or 0) > 0 or (student.sdf_amount_paid or 0) > 0 or (student.boarding_amount_paid or 0) > 0:
                    class_analysis[class_name]['partial_payments'] += 1
                else:
                    class_analysis[class_name]['no_payments'] += 1
                
                class_analysis[class_name]['total_required'] += (student.pta_amount_required or 0) + (student.sdf_amount_required or 0) + (student.boarding_amount_required or 0)
                class_analysis[class_name]['total_collected'] += (student.pta_amount_paid or 0) + (student.sdf_amount_paid or 0) + (student.boarding_amount_paid or 0)
            
            # Calculate collection rates for each class
            for class_name in class_analysis:
                if class_analysis[class_name]['total_required'] > 0:
                    class_analysis[class_name]['collection_rate'] = round(
                        (class_analysis[class_name]['total_collected'] / class_analysis[class_name]['total_required']) * 100, 2
                    )
                else:
                    class_analysis[class_name]['collection_rate'] = 0
            
            return jsonify({
                'total_students': total_students,
                'paid_in_full': paid_in_full,
                'partial_payments': partial_payments,
                'no_payments': no_payments,
                'collection_rate': round((total_collected / total_required * 100) if total_required > 0 else 0, 2),
                'total_required': float(total_required),
                'total_collected': float(total_collected),
                'total_outstanding': float(total_outstanding),
                'fund_analysis': {k: {
                    'required': float(v['required']),
                    'collected': float(v['collected']),
                    'outstanding': float(v['outstanding']),
                    'collection_rate': v['collection_rate']
                } for k, v in fund_analysis.items()},
                'class_analysis': {k: {
                    'total_students': v['total_students'],
                    'paid_in_full': v['paid_in_full'],
                    'partial_payments': v['partial_payments'],
                    'no_payments': v['no_payments'],
                    'total_required': float(v['total_required']),
                    'total_collected': float(v['total_collected']),
                    'collection_rate': v['collection_rate']
                } for k, v in class_analysis.items()}
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/analytics/recent-activity')
    @login_required
    def api_recent_activity():
        """Get recent payment and expenditure activity"""
        try:
            current_school_id = get_current_school_id()
            limit = int(request.args.get('limit', 20))
            
            # Get recent payments
            if current_school_id:
                recent_payments = Income.query.filter_by(school_id=current_school_id)\
                    .order_by(Income.payment_date.desc(), Income.id.desc())\
                    .limit(limit).all()
                
                recent_expenditures = Expenditure.query.filter_by(school_id=current_school_id)\
                    .order_by(Expenditure.date.desc(), Expenditure.id.desc())\
                    .limit(limit).all()
            else:
                recent_payments = Income.query\
                    .order_by(Income.payment_date.desc(), Income.id.desc())\
                    .limit(limit).all()
                
                recent_expenditures = Expenditure.query\
                    .order_by(Expenditure.date.desc(), Expenditure.id.desc())\
                    .limit(limit).all()
            
            # Format payment data
            payments_data = []
            for payment in recent_payments:
                payments_data.append({
                    'id': payment.id,
                    'date': payment.payment_date.strftime('%Y-%m-%d'),
                    'time': payment.payment_date.strftime('%H:%M') if hasattr(payment, 'payment_time') else '00:00',
                    'student_id': payment.student_id,
                    'student_name': getattr(payment, 'student_name', 'N/A'),
                    'amount': float(payment.amount_paid),
                    'fund_type': payment.fund_type,
                    'type': 'income'
                })
            
            # Format expenditure data
            expenditures_data = []
            for expenditure in recent_expenditures:
                expenditures_data.append({
                    'id': expenditure.id,
                    'date': expenditure.date.strftime('%Y-%m-%d'),
                    'time': '00:00',  # Expenditures typically don't have time
                    'description': expenditure.activity_description,
                    'amount': float(expenditure.amount_paid),
                    'fund_type': expenditure.fund_type,
                    'type': 'expenditure'
                })
            
            # Combine and sort by date
            all_activities = payments_data + expenditures_data
            all_activities.sort(key=lambda x: x['date'], reverse=True)
            
            return jsonify({
                'recent_activities': all_activities[:limit],
                'payments_count': len(payments_data),
                'expenditures_count': len(expenditures_data)
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return app