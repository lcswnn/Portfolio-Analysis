#main Flask app for Web app
import io
from flask import Flask, render_template, Response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import analytics

app = Flask(__name__)

@app.route('/')
def index():
    # Generate the animated timeline graph
    graph_html = analytics.create_animated_timeline_graph()
    return render_template('index.html', graph_html=graph_html)

@app.route('/about.html')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)