#imports
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import sqlite3

#set Plotly to render charts using the browser
pio.renderers.default = "browser"

def get_portfolio_timeline_data():
    """Fetch portfolio total value over time from database"""
    conn = sqlite3.connect('data/positions.db')

    # Query to get account total for each date
    query = """
    SELECT Date,
           REPLACE(REPLACE("Mkt Val (Market Value)", '$', ''), ',', '') as portfolio_value
    FROM positions
    WHERE Symbol = 'Account Total'
    ORDER BY Date
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    # Convert portfolio_value to numeric
    df['portfolio_value'] = pd.to_numeric(df['portfolio_value'])
    df['Date'] = pd.to_datetime(df['Date'])

    # Sort by date to ensure chronological order
    df = df.sort_values('Date').reset_index(drop=True)

    return df

def create_animated_timeline_graph():
    """Create an animated line graph showing portfolio growth over time with smooth CSS animation"""
    df = get_portfolio_timeline_data()

    # Create the complete figure with all data
    fig = go.Figure()

    # Add the main line trace with all data
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['portfolio_value'],
        mode='lines+markers',
        line=dict(color='#293949', width=3, shape='spline', smoothing=1.3),
        marker=dict(size=8, color='#293949'),
        fill='tozeroy',
        fillcolor='rgba(41, 57, 73, 0.1)',
        name='Portfolio Value'
    ))

    # Update layout with fixed axis ranges
    fig.update_layout(
        title={
            'text': 'Portfolio Value Over Time',
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=24, color='white', family='ClashDisplay'),
        },
        xaxis=dict(
            title=dict(text='Date', font=dict(size=14, color='white', family='ClashDisplay')),
            tickfont=dict(color='white'),
            gridcolor='rgba(255, 255, 255, 0.1)',
            showgrid=True,
            range=[df['Date'].min(), df['Date'].max()]
        ),
        yaxis=dict(
            title=dict(text='Portfolio Value ($)', font=dict(size=14, color='white', family='ClashDisplay')),
            tickfont=dict(color='white', family='ClashDisplay'),
            tickformat='$,.0f',
            gridcolor='rgba(255, 255, 255, 0.1)',
            showgrid=True,
            range=[0, df['portfolio_value'].max() * 1.1]
        ),
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        font=dict(color='white', family='ClashDisplay'),
        hovermode='x unified'
    )

    # Convert to HTML with custom JavaScript for smooth animation
    html = fig.to_html(include_plotlyjs='cdn', div_id='animated-timeline')

    # Add custom JavaScript for smooth SVG path animation
    animation_script = """
    <style>
        #animated-timeline .scatterlayer path.js-line {
            stroke-dasharray: 3000;
            stroke-dashoffset: 3000;
            animation: dash 6.6s ease-in-out forwards;
        }

        #animated-timeline .scatterlayer path.js-fill {
            opacity: 0;
            animation: fillFade 4.7s ease-in-out forwards;
        }

        #animated-timeline .scatterlayer .point {
            opacity: 0;
            animation: pointFade 5s ease-in-out forwards;
        }

        @keyframes dash {
            to {
                stroke-dashoffset: 0;
            }
        }

        @keyframes fillFade {
            0% {
                opacity: 0;
            }
            50% {
                opacity: 0;
            }
            100% {
                opacity: 1;
            }
        }

        @keyframes pointFade {
            0% {
                opacity: 0;
            }
            70% {
                opacity: 0;
            }
            100% {
                opacity: 1;
            }
        }
    </style>
    """

    # Insert the animation script before the closing body tag
    html = html.replace('</body>', animation_script + '</body>')

    return html

