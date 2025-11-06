#main Flask app for Web app
import io
from flask import Flask, render_template, Response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import analytics

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/returns.png')
def returns_png():
    fig = analytics.graph_data()
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

@app.route('/pie.png')
def pie_png():
    fig = analytics.graph_allocation()
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)