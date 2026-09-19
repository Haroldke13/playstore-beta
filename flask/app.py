import os
from qa_companion import create_app

config = {'SECRET_KEY': os.getenv('SECRET_KEY', 'dev-change-me')}
if os.getenv('DATABASE_PATH'):
    config['DATABASE'] = os.getenv('DATABASE_PATH')

app = create_app(config)

if __name__ == '__main__':
    app.run(
        host=os.getenv('HOST', '127.0.0.1'),
        port=int(os.getenv('PORT', '5000')),
        debug=os.getenv('FLASK_DEBUG', '0') == '1',
    )