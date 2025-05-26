#!/usr/bin/python3
from app import app
#  @formatter:off
from endpoints import routes
#  @formatter:on

if __name__ == '__main__':
    # app.debug = True
    app.run(host='0.0.0.0', port=5000, use_reloader=False)
