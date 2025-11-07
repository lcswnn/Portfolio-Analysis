#main Flask app for Web app
from flask import Flask, render_template
import analytics

app = Flask(__name__)

@app.route('/')
def index():
    # Generate the animated timeline graph
    graph_html = analytics.create_animated_timeline_graph()
    return render_template('index.html', graph_html=graph_html)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

if __name__ == '__main__':
    app.run(debug=True)