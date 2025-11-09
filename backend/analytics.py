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
        REPLACE(REPLACE(Mkt_Val , '$', ''), ',', '') as portfolio_value
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

def get_FAKE_portfolio_timeline_data():
    """Fetch portfolio total value over time from database"""
    conn = sqlite3.connect('data/dummy_positions.db')

    # Query to get account total for each date
    query = """
    SELECT Date,
        REPLACE(REPLACE(`Mkt Val (Market Value)`, '$', ''), ',', '') as portfolio_value
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
            'text': 'Your Portfolio Value Over Time',
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=24, color='#F9F9F9', family='ClashDisplay'),
        },
        xaxis=dict(
            title=dict(text='Date', font=dict(size=14, color='#F9F9F9', family='ClashDisplay')),
            tickfont=dict(color='#F9F9F9'),
            gridcolor='rgba(255, 255, 255, 0.1)',
            showgrid=True,
            range=[df['Date'].min(), df['Date'].max()],
            showspikes=True,
            spikemode='across',
            spikesnap='data',
            spikecolor='rgba(249, 249, 249, 0.4)',
            spikethickness=1,
            spikedash='dot'
        ),
        yaxis=dict(
            title=dict(text='Portfolio Value ($)', font=dict(size=14, color='#F9F9F9', family='ClashDisplay')),
            tickfont=dict(color='#F9F9F9', family='ClashDisplay'),
            tickformat='$,.0f',
            gridcolor='rgba(255, 255, 255, 0.1)',
            showgrid=True,
            range=[0, df['portfolio_value'].max() * 1.1]
        ),
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        font=dict(color='#F9F9F9', family='ClashDisplay'),
        hovermode='x unified'
    )

    # Convert to HTML with custom JavaScript for smooth animation
    html = fig.to_html(
        include_plotlyjs='cdn',
        div_id='animated-timeline',
        config={'displayModeBar': False}
    )

    # Add custom JavaScript for smooth SVG path animation
    animation_script = """
    <style>
        #animated-timeline .scatterlayer path.js-line {
            stroke-dasharray: 3000;
            stroke-dashoffset: 3000;
            animation: dash 6s ease-in-out forwards;
        }

        #animated-timeline .scatterlayer path.js-fill {
            opacity: 0;
            animation: fillFade 3s ease-in-out forwards;
        }

        #animated-timeline .scatterlayer .point {
            opacity: 0;
            animation: pointFade 3s ease-in-out forwards;
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
    html = html.replace('</body>', f'{animation_script}</body>')

    return html


def get_holdings_by_type():
    """Fetch holdings aggregated by Security_Type over time from database"""
    conn = sqlite3.connect('data/positions.db')

    # Query to get market value by security type for each date
    query = """
    SELECT Date,
        Security_Type,
        SUM(CAST(REPLACE(REPLACE(Mkt_Val, '$', ''), ',', '') AS FLOAT)) as total_value
    FROM positions
    WHERE Symbol != 'Account Total' AND Security_Type IS NOT NULL AND Security_Type != ''
    GROUP BY Date, Security_Type
    ORDER BY Date, Security_Type
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    # Convert to numeric and datetime
    df['total_value'] = pd.to_numeric(df['total_value'], errors='coerce')
    df['Date'] = pd.to_datetime(df['Date'])

    # Remove rows with null values
    df = df.dropna()

    # Sort by date
    df = df.sort_values('Date').reset_index(drop=True)

    return df

def create_holdings_by_type_graph():
    """Create an animated pie chart showing distribution of holdings by security type"""
    df = get_holdings_by_type()

    if df.empty:
        # Return empty graph if no data
        fig = go.Figure()
        fig.update_layout(
            title={
                'text': 'Holdings by Type - No Data Available',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=24, color='#F9F9F9', family='ClashDisplay'),
            },
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            font=dict(color='#F9F9F9', family='ClashDisplay'),
        )
        return fig.to_html(
            include_plotlyjs='cdn',
            div_id='holdings-pie',
            config={'displayModeBar': False},
        )

    # Get the most recent date data
    latest_date = df['Date'].max()
    latest_data = df[df['Date'] == latest_date]

    # Color palette for different security types
    colors = {
        'Equity': "#FAEDCB",
        'Mutual Fund': '#C9E4DE',
        'ETFs & Closed End Funds': '#C6DEF1',
        'Cash and Money Market': '#DBCDF0',
        'Cryptocurrency': '#F2C6DE',
        '--': '#F7D9C4',
        'Other': '#7E8586'
    }

    # Prepare data for pie chart
    labels = latest_data['Security_Type'].tolist()
    values = latest_data['total_value'].tolist()
    pie_colors = [colors.get(label, f'hsl({(idx * 360 / len(labels))}, 100%, 50%)')
                for idx, label in enumerate(labels)]

    # Create figure with full data
    fig = go.Figure(
        data=[go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=pie_colors),
            textposition='auto',
            textinfo='label+percent',
            textfont=dict(size=12, color='#293949', family='ClashDisplay'),
            hoverinfo='label+value+percent',
        )]
    )

    # Update layout
    fig.update_layout(
        title={
            'text': f'Holdings by Security Type (as of {latest_date.strftime("%m/%d/%Y")})',
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=28, color='#F9F9F9', family='ClashDisplay', weight='bold' ),
        },
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        font=dict(color='#F9F9F9', family='ClashDisplay'),
        showlegend=True,
        legend=dict(
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.01,
            bgcolor='rgba(41, 57, 73, 0.7)',
            bordercolor='rgba(249, 249, 249, 0.2)',
            borderwidth=1
        ),
        margin=dict(l=20, r=250, t=60, b=10)
    )

    # Convert to HTML
    html = fig.to_html(
        include_plotlyjs='cdn',
        div_id='holdings-pie',
        config={'displayModeBar': False, 'responsive': True}
    )

    # Add smooth CSS animation for pie chart
    animation_script = """
    <style>
        #holdings-pie {
            animation: chartFadeIn 0.6s ease-out forwards;
        }

        #holdings-pie .pie {
            animation: pieSpin 2s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
            transform-origin: center;
            font-family: 'ClashDisplay', sans-serif;
        }

        #holdings-pie .slicepath {
            animation: sliceFade 1.8s ease-out 0.2s forwards;
            opacity: 0;
        }

        #holdings-pie text {
            opacity: 1;
            font-family: 'ClashDisplay', sans-serif;
        }

        #holdings-pie .legendlayer text,
        #holdings-pie .legendlayer path {
            animation: legendFade 0.8s ease-out 1.4s forwards;
            opacity: 0;
            font-family: 'ClashDisplay', sans-serif;
        }

        #holdings-pie .legendlayer g {
            transform: translate(10px, 0);
        }

        #holdings-pie .legendlayer text {
            dy: 0.35em;
        }

        #holdings-pie .hovertext {
            animation: none !important;
            opacity: 1 !important;
            font-family: 'ClashDisplay', sans-serif !important;
        }

        #holdings-pie .hovertext tspan {
            font-family: 'ClashDisplay', sans-serif !important;
        }

        @keyframes chartFadeIn {
            0% {
                opacity: 0;
                transform: translateY(30px);
            }
            100% {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes pieSpin {
            0% {
                opacity: 0;
                transform: scale(0.3) rotateZ(-360deg);
            }
            40% {
                opacity: 1;
            }
            100% {
                opacity: 1;
                transform: scale(1) rotateZ(0deg);
            }
        }

        @keyframes sliceFade {
            0% {
                opacity: 0;
                filter: brightness(0.7);
            }
            100% {
                opacity: 1;
                filter: brightness(1);
            }
        }

        @keyframes textFade {
            0% {
                opacity: 0;
            }
            100% {
                opacity: 1;
            }
        }

        @keyframes legendFade {
            0% {
                opacity: 0;
                transform: translateX(10px);
            }
            100% {
                opacity: 1;
                transform: translateX(0);
            }
        }
    </style>
    """

    # Insert the animation script before the closing body tag
    html = html.replace('</body>', f'{animation_script}</body>')

    return html

def create_DUMMY_animated_timeline_graph():
    """Create an animated line graph showing portfolio growth over time with smooth CSS animation"""
    df = get_FAKE_portfolio_timeline_data()

    # Create the complete figure with all data
    fig = go.Figure()

    # Add the main line trace with all data (no hover text)
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['portfolio_value'],
        mode='lines',
        line=dict(color='#293949', width=3, shape='spline', smoothing=1.3),
        fill='tozeroy',
        fillcolor='rgba(41, 57, 73, 0.1)',
        name='Portfolio Value',
        hoverinfo='skip'
    ))

    # Update layout with fixed axis ranges
    fig.update_layout(
        title={
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=24, color='#F9F9F9', family='ClashDisplay'),
        },
        xaxis=dict(
            title=dict(text='Date', font=dict(size=14, color='#F9F9F9', family='ClashDisplay')),
            tickfont=dict(color='#F9F9F9'),
            gridcolor='rgba(255, 255, 255, 0.1)',
            showgrid=True,
            range=[df['Date'].min(), df['Date'].max()],
            showspikes=False
        ),
        yaxis=dict(
            title=dict(text='Portfolio Value ($)', font=dict(size=14, color='#F9F9F9', family='ClashDisplay')),
            tickfont=dict(color='#F9F9F9', family='ClashDisplay'),
            tickformat='$,.0f',
            gridcolor='rgba(255, 255, 255, 0.1)',
            showgrid=True,
            showticklabels=False,
            range=[0, df['portfolio_value'].max() * 1.1]
        ),
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        font=dict(color='#F9F9F9', family='ClashDisplay'),
        hovermode='closest'
    )

    # Convert to HTML with custom JavaScript for smooth animation
    html = fig.to_html(
        include_plotlyjs='cdn',
        div_id='animated-timeline',
        config={'displayModeBar': False}
    )

    # Add custom JavaScript for smooth SVG path animation
    animation_script = """
    <style>
        #animated-timeline .scatterlayer path.js-line {
            stroke-dasharray: 3000;
            stroke-dashoffset: 3000;
            animation: dash 6s ease-in-out forwards;
        }

        #animated-timeline .scatterlayer path.js-fill {
            opacity: 0;
            animation: fillFade 3s ease-in-out forwards;
        }

        #animated-timeline .scatterlayer .point {
            opacity: 0;
            animation: pointFade 3s ease-in-out forwards;
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
    html = html.replace('</body>', f'{animation_script}</body>')

    return html

