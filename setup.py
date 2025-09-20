from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="smartfee-revenue",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="SmartFee Revenue Management System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/smartfee-revenue",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Flask==2.3.3',
        'Flask-SQLAlchemy==3.0.5',
        'Flask-WTF==1.2.1',
        'python-dotenv==1.0.0',
        'SQLAlchemy==2.0.43',
        'WTForms==3.0.1',
        'Werkzeug==2.3.7',
        'gunicorn==21.2.0',
        'eventlet==0.33.3',  # Using eventlet instead of gevent
        'psycopg2-binary==2.9.9',
        'bcrypt==4.0.1',
        'python-jose==3.3.0',
        'cffi==1.16.0',
        'pycparser==2.21',
    ],
    python_requires='>=3.9',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'smartfee=wsgi:main',
        ],
    },
)
