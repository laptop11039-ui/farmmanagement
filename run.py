import os
from app import create_app, db
from app.models import User

app = create_app(os.environ.get('FLASK_ENV', 'development'))

@app.shell_context_processor
def make_shell_context():
    return {'db': db}

@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    print('Database initialized.')

@app.cli.command()
def create_admin():
    """Create an admin user."""
    from getpass import getpass
    username = input('Enter admin username: ')
    email = input('Enter admin email: ')
    password = getpass('Enter admin password: ')
    
    if User.query.filter_by(username=username).first():
        print('Admin user already exists!')
        return
    
    admin = User(username=username, email=email, is_admin=True)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    
    print(f'Admin user {username} created successfully!')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
