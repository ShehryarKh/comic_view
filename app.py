from flask import Flask
app = Flask(__name__)




@app.route("/")
def main():
    return "Comic View Coming Soon"




if __name__ == "__name__":
		app.run()
