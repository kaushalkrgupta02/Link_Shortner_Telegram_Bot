from flask import Flask
app = flask(__name__)

@app.route('/')
def hello_world():
    return 'Lokesh'

if __name__ == "__main__":
    app.run()