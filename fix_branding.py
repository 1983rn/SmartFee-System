#!/usr/bin/env python3
"""
Fix branding issues in SmartFee Revenue Collection System
"""

from app import app, db, SchoolConfiguration

def fix_branding():
    with app.app_context():
        # Update any existing school configuration that might have wrong name
        configs = SchoolConfiguration.query.all()
        
        for config in configs:
            if 'Malawi' in config.school_name or 'Reporting' in config.school_name:
                print(f"Found incorrect school name: {config.school_name}")
                config.school_name = 'SmartFee Revenue Collection System'
                config.is_active = True
                db.session.commit()
                print("Updated to: SmartFee Revenue Collection System")
            else:
                print(f"Current school name: {config.school_name}")
        
        # Ensure there's at least one active configuration
        active_config = SchoolConfiguration.query.filter_by(is_active=True).first()
        if not active_config:
            new_config = SchoolConfiguration(
                school_name='SmartFee Revenue Collection System',
                is_active=True
            )
            db.session.add(new_config)
            db.session.commit()
            print("Created new default configuration")

if __name__ == '__main__':
    fix_branding()
    print("Branding fix completed!")