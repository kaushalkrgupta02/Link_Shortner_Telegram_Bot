from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Your Code is running'

if __name__ == "__main__":
    app.run()
